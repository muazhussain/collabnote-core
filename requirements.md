# CollabNote - Infrastructure Requirements

## A. Services

| Service | Image | Host Port | Internal Port |
|---|---|---|---|
| Postgres | `postgres:16-alpine` | 5432 | 5432 |
| Mongo | `mongo:7` | 27017 | 27017 |
| Redis | `redis:7-alpine` | 6379 | 6379 |
| Elasticsearch | `elasticsearch:8.11.1` | 9200 | 9200 |
| Kafka (KRaft) | `confluentinc/cp-kafka:7.6.0` | 9092 | 9092, 9093 |
| api1 | local build | - | 8000 |
| api2 | local build | - | 8000 |
| consumer | local build | - | - |
| nginx | `nginx:1.25-alpine` | 80 | 80 |

`api1`, `api2`, and `consumer` are not exposed to the host. Nginx is the only public entry point. DB ports are exposed in dev for local inspection; remove in prod.

---

## B. Resource Estimate

| Service | RAM (MB) | CPU |
|---|---|---|
| Elasticsearch | 1024 | 0.75 |
| Kafka | 1024 | 0.5 |
| Mongo | 512 | 0.25 |
| Postgres | 256 | 0.25 |
| api1 + api2 | 512 | 0.5 |
| consumer | 128 | 0.1 |
| Redis | 128 | 0.1 |
| Nginx | 32 | 0.1 |
| OS + dockerd | 1024 | 0.5 |
| **Total** | **~4640** | **~3.1** |

**VM: 6 GB RAM, 4 vCPU, 20 GB disk.**

---

## C. Data Model

### Postgres - `users`

| Column | Type | Constraints |
|---|---|---|
| `id` | `INTEGER` | PK, autoincrement |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL |
| `username` | `VARCHAR(50)` | UNIQUE, NOT NULL |
| `password_hash` | `VARCHAR(255)` | NOT NULL |
| `created_at` | `TIMESTAMP` | NOT NULL, default `NOW()` |
| `is_active` | `BOOLEAN` | NOT NULL, default `TRUE` - added in migration 2 |

### Mongo - `notes`

| Field | Type | Notes |
|---|---|---|
| `_id` | `ObjectId` | |
| `user_id` | `int` | refs `users.id` |
| `title` | `string` | ES-indexed, 3× boost |
| `content` | `string` | ES-indexed |
| `tags` | `string[]` | ES-indexed |
| `created_at` | `datetime` | |
| `updated_at` | `datetime` | set on PUT |

### Mongo - `activity_logs`

| Field | Type | Notes |
|---|---|---|
| `_id` | `ObjectId` | |
| `event_type` | `string` | `user_signup` \| `user_login` \| `note_created` \| `note_updated` \| `note_deleted` \| `note_searched` |
| `user_id` | `int` | |
| `resource_id` | `string \| null` | note `_id` as string; null for auth events |
| `timestamp` | `datetime` | producer-side |
| `metadata` | `object` | per-event payload |

Append-only. Written exclusively by the Kafka consumer.

### Ownership

| Data | Owner | Notes |
|---|---|---|
| Identity / credentials | Postgres | Transactional, unique constraints |
| Notes | Mongo | Variable shape, embedded tags |
| Activity events | Mongo | Append-only sink |
| Search index | Elasticsearch | Derived from Mongo, rebuildable |
| Hot reads | Redis | Derived, TTL 3600s |
| Event stream | Kafka `collabnote_events` | In-flight only |

The hybrid endpoint `GET /users/{user_id}/notes` is the only cross-store path: existence check in Postgres, fetch from Mongo by `user_id`.

---

## D. Endpoints

### REST

#### Phase 1 - Auth, Users, Notes

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/signup` | - | Register user; hash password; store in Postgres |
| POST | `/auth/login` | - | Verify credentials; return JWT |
| POST | `/auth/refresh` | JWT | Issue a new token; validates existing before expiry |
| POST | `/auth/logout` | JWT | Add token JTI to Redis deny-list; effective revocation |
| GET | `/profile` | JWT | Return authenticated user's own profile |
| PATCH | `/profile` | JWT | Update own `username` or `email` in Postgres |
| GET | `/users/{user_id}` | JWT | Public profile lookup by Postgres ID |
| GET | `/users/{user_id}/notes` | JWT | Verify user in Postgres; fetch their notes from Mongo |
| POST | `/notes` | JWT | Create note; stored in Mongo |
| GET | `/notes` | JWT | List authenticated user's notes; supports `?tags=&page=&limit=` |
| GET | `/notes/{id}` | JWT | Fetch single note by ObjectId |
| PUT | `/notes/{id}` | JWT (owner) | Full update of note fields |
| DELETE | `/notes/{id}` | JWT (owner) | Delete note |
| POST | `/notes/{id}/tags` | JWT (owner) | Append tags to a note without a full PUT |
| DELETE | `/notes/{id}/tags/{tag}` | JWT (owner) | Remove a single tag from a note |

#### Phase 2 - Search and Caching

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/search` | JWT | `?q={term}` - fuzzy `multi_match` across title (3× boost) and content; returns ranked results with highlighted snippets. Accepts `?tags=` to pre-filter |

Existing note POST/PUT/DELETE gain ES indexing and Redis key invalidation. GET `/notes/{id}` gains Redis read-through (`note:{id}`, TTL 3600s).

#### Phase 3 - Event Streaming

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/activity` | JWT | Last 20 activity log entries for the authenticated user, newest first. Accepts `?event_type=` filter |

All auth and note endpoints publish a non-blocking event to `collabnote_events` on success.

#### Phase 5 - Ops

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | - | Liveness probe; returns `200 OK` and `X-Instance-ID` header |
| GET | `/health/ready` | - | Readiness probe; checks Postgres, Mongo, Redis, ES connections before responding |

---

### GraphQL - `/graphql`

Implemented with Strawberry. Auth reads `Authorization: Bearer <token>` from the request context; resolvers for user-scoped data return a 401-equivalent GraphQL error if no valid token is present.

#### Schema

```graphql
type User {
  id: ID!
  username: String!
  email: String!
  createdAt: String!
  notes: [Note!]!
  activityLogs: [ActivityLog!]!
}

type Note {
  id: ID!
  userId: Int!
  title: String!
  content: String!
  tags: [String!]!
  createdAt: String!
  updatedAt: String
  author: User!
}

type ActivityLog {
  id: ID!
  eventType: String!
  userId: Int!
  resourceId: String
  timestamp: String!
  metadata: JSON
}

type Query {
  me: User!
  user(id: ID!): User!
  users: [User!]!
  note(id: ID!): Note!
  notes: [Note!]!
}

type Mutation {
  createNote(title: String!, content: String!, tags: [String!]!): Note!
  updateNote(id: ID!, title: String, content: String, tags: [String!]): Note!
  deleteNote(id: ID!): Boolean!
  updateUser(id: ID!, username: String, email: String): User!
}
```

#### Dashboard Query

```graphql
query CollabNoteDashboard {
  me {
    username
    email
    notes {
      title
      tags
      createdAt
    }
    activityLogs {
      eventType
      timestamp
    }
  }
}
```

`createNote`, `updateNote`, and `deleteNote` are fully consistent with their REST counterparts - same Mongo write, ES index, Redis invalidation, and Kafka event.

---

## E. Architecture Decision Log

---

#### ADR-1 - Notes in MongoDB, not PostgreSQL

**Context:** Notes have a freeform `content` field, a variable `tags` array, and may gain more optional fields over time.

**Decision:** Store notes as Mongo documents. Postgres holds only `users`.

**Rationale:** A relational schema requires a `notes_tags` join table or a `text[]` column - both add friction to the write path and the ES indexing pipeline. The document model fits the data naturally. Relational consistency matters for auth (unique emails, transactional logins), not for note content.

---

#### ADR-2 - Redis TTL of 3600 seconds, not indefinite

**Context:** `GET /notes/{id}` caches the result under key `note:{id}`. PUT and DELETE invalidate it explicitly.

**Decision:** Every cache entry expires after one hour regardless of explicit invalidation.

**Rationale:** Invalidation only works if the delete runs successfully on every write, every time. An unhandled exception or a mid-deploy request can silently skip it, leaving a stale entry forever. The TTL is a safety net - worst-case staleness is bounded to one hour even when invalidation fails.

---

#### ADR-3 - Kafka consumer as a separate process

**Context:** Events on `collabnote_events` need to be written to `activity_logs`. The easy option is an `aiokafka` task inside FastAPI's startup hook.

**Decision:** Consumer runs as its own container (`python -m consumer.consumer`).

**Rationale:** An in-process consumer dies when the API restarts and creates duplicate reads when two API instances both consume the same partition. A separate process restarts independently, commits offsets cleanly, and keeps the API's event loop free of long-running background work.

---

#### ADR-4 - JWT over server-side sessions

**Context:** Phase 5 runs two API instances behind Nginx round-robin. Any request can land on either instance.

**Decision:** HS256 JWT Bearer tokens, 30-minute expiry, with a `POST /auth/refresh` endpoint and a Redis JTI deny-list for logout.

**Rationale:** Sessions need sticky routing or a shared session store - both add complexity. JWTs are self-contained and validate locally on either instance with no coordination. The deny-list handles logout without server-side state; the key auto-expires when the token would have expired anyway.

---

#### ADR-5 - Elasticsearch `multi_match` with title boost and `fuzziness: AUTO`

**Context:** Search needs to return relevant results even with typos. Notes have two text fields: `title` and `content`.

**Decision:** `multi_match` across `title` (boost `^3`) and `content`, `fuzziness: AUTO`, with highlighted snippets on both fields.

**Rationale:** A plain `match` on combined text loses per-field scoring. Boosting `title` ranks notes where the search term appears in the title above those that only mention it in the body, which is the expected behaviour. `fuzziness: AUTO` handles typos proportional to word length without over-fuzzing short terms.