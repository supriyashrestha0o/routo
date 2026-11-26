# Route Backend API

All `/api/` endpoints use the `{ "success": true, "data": ... }` response envelope. Errors use `{ "success": false, "error": ..., "status": ... }`, including unexpected server errors. Send `Authorization: Bearer <Firebase ID token>` on every `/api/` endpoint. Firebase ID tokens are verified by Django; Flutter must never contain a Firebase service account key.

## Setup

1. Create a Python 3.13 virtual environment and install `requirements.txt`.
2. Copy `.env.example` to `.env` and configure all required values.
3. Create the MySQL 8 database and apply migrations with `python manage.py migrate`.
4. Start the development server with `python manage.py runserver 0.0.0.0:8000`.

For two phones, set `DJANGO_ALLOWED_HOSTS` to the backend host/IP and use the same reachable base URL on both phones. `localhost` on a phone means that phone itself.

Production mode fails closed when `DJANGO_SECRET_KEY`, Firebase credentials, or Cloudinary credentials are missing. Rotate credentials that have previously been committed to source control before deploying.

## Health and readiness

- `GET /` — liveness response.
- `GET /health` — readiness response. It checks the database and verifies that Firebase and Cloudinary are configured. It returns HTTP 503 with a `degraded` status when any required dependency is unavailable.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/accounts/link/` | Link the verified Firebase identity (created on first authenticated request) |
| GET | `/api/accounts/me/` | Current account |
| GET, PUT, PATCH | `/api/profiles/me/` | Read/create or update own profile |
| POST | `/api/profiles/me/image/` | Upload or replace own profile picture |
| GET, POST | `/api/journeys/` | List/search open journeys or create one as the authenticated driver |
| GET, PUT, PATCH | `/api/journeys/{id}/` | Read or update; only the owner may update |
| POST | `/api/journeys/{id}/cancel/` | Cancel own journey and cancel affected requests |
| POST | `/api/journeys/{id}/complete/` | Complete own journey after its departure time |
| POST | `/api/ride-requests/` | Request seats on a journey |
| GET | `/api/ride-requests/mine/` | Passenger's requests and current statuses |
| GET | `/api/ride-requests/journeys/{journey_id}/` | Requests for a journey owned by the current driver |
| POST | `/api/ride-requests/{id}/accept/` | Accept a pending request (owner only) |
| POST | `/api/ride-requests/{id}/reject/` | Reject a pending request (owner only) |
| POST | `/api/ride-requests/{id}/cancel/` | Cancel the passenger's own pending or accepted request |
| GET | `/api/matches/` | Matches involving the current user |
| GET, POST | `/api/notifications/devices/` | List/register own FCM device token |
| DELETE | `/api/notifications/devices/{id}/` | Remove own device token |
| GET, POST | `/api/reviews/` | List own authored reviews (or `?user={id}` for received reviews) / create a review |
| GET, POST | `/api/reports/` | List own reports / file a report |

## Journeys and ride requests

Journey search accepts optional `?origin=...&destination=...` substring filters. Journey fields on create are `origin`, `destination`, `departure_time` (ISO 8601), `total_seats`, and optional `notes`. Available seats are initialized by the server.

```json
{
  "origin": "Patan",
  "destination": "Kirtipur",
  "departure_time": "2026-12-01T08:30:00+05:45",
  "total_seats": 3,
  "notes": "Meet at the main gate"
}
```

Origin and destination must differ, departure must be in the future, and seat counts must be between 1 and 65,535. Journey updates lock the journey row, so concurrent accept decisions cannot be overwritten by a stale seat count. Increasing capacity reopens a full journey; reducing capacity cannot go below accepted requests.

A ride request body is `{ "journey": 12, "seats_requested": 1 }`. Seat counts must be between 1 and 65,535, and departed or unavailable journeys cannot be requested. Request status is server-controlled (`pending`, `accepted`, `rejected`, `cancelled`). Accepting locks the journey row in a database transaction, decrements seats, and creates a match atomically. A unique journey/passenger constraint prevents duplicate requests.

Cancelling a journey cancels pending and accepted requests, removes their matches, and releases the journey. Cancelling an accepted passenger request restores its seats and removes the match. Completing a journey is available after its scheduled departure, cancels pending requests, and preserves accepted matches.

## Profiles and image uploads

A profile body contains `full_name`, `phone_number`, `university`, `student_id`, and `is_driver`. Profile responses include `profile_image_url` (empty until an image is uploaded).

Send `POST /api/profiles/me/image/` with the Firebase ID token in the Bearer authorization header and a `multipart/form-data` file field named `image`. JPEG, PNG, and WebP image contents are accepted, up to `PROFILE_IMAGE_MAX_BYTES` (5 MiB by default). The server inspects the actual image data, uploads it to Cloudinary over HTTPS, and stores the resulting secure URL and Cloudinary public ID in the authenticated user's profile row. The public ID stays server-side for replacement cleanup; API responses expose only the image URL.

```json
{
  "success": true,
  "data": {
    "message": "Profile image uploaded successfully",
    "profile_image": "https://res.cloudinary.com/example/image/upload/route/profile_images/example.jpg"
  }
}
```

When replacing an image, the profile row is updated to the new Cloudinary URL first; the previous Cloudinary asset is then deleted. If old-asset cleanup fails, the new database reference remains valid and the old asset may need later cleanup.

## Device tokens

Register an FCM registration token with `{ "token": "FCM registration token", "platform": "android" }`. Registration is idempotent: re-registering a token returns the existing token id, updates its platform, reactivates it, and transfers ownership to the current account.

## Reviews and reports

A review must reference a completed journey. The reviewer must be the journey driver or an accepted matched passenger, and the reviewed user must be the counterpart. Self-reviews, unrelated users, incomplete journeys, and duplicate reviews are rejected.

```json
{
  "reviewed_user": 4,
  "journey": 12,
  "rating": 5,
  "comment": "On time"
}
```

A report body is `{ "reported_user": 4, "journey": 12, "description": "..." }`. A user cannot report themselves.

## Phone workflow

1. Each phone signs in with Firebase Auth and sends its current ID token as a Bearer token.
2. The driver registers its FCM token, then POSTs a journey to `/api/journeys/`.
3. A passenger GETs `/api/journeys/`, then POSTs to `/api/ride-requests/`.
4. Django saves request state in MySQL and sends FCM to the driver's registered devices.
5. The driver GETs `/api/ride-requests/journeys/{id}/` and accepts or rejects the request.
6. The passenger GETs `/api/ride-requests/mine/` to see status; both can GET `/api/matches/`.
7. The driver completes the journey after departure. Accepted participants can then review each other.

Push delivery requires a valid Firebase Admin service-account file on the Django server and registered device tokens. Ride data stays in the configured database; Firestore is not used by this backend.

## Report administration

In Django admin, open **Reports**, select report rows, and choose **Delete selected reported users and all of their reports**. The action requires both report-deletion and Firebase-user-deletion permissions. Before deleting a user, the backend stores a Firebase identity tombstone so a valid token cannot automatically recreate the blocked account.

## Errors and limits

Validation errors return HTTP 400, ownership violations return 403, missing resources return 404, oversized request bodies return 413, and unexpected server errors return a JSON HTTP 500 response. Authentication failures return 401. API traffic is throttled using the rates configured by `API_ANON_RATE` and `API_USER_RATE`.
