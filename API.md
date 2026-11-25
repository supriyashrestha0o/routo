# Route Backend API

All endpoints use the `/api/` prefix and successful responses use `{ "success": true, "data": ... }`. Errors use `{ "success": false, "error": ..., "status": ... }`. Send `Authorization: Bearer <Firebase ID token>` on every endpoint. Firebase ID tokens are verified by Django; Flutter must never contain a Firebase service account key.

Configure `.env` values from `.env.example`, install `requirements.txt`, create the MySQL 8 database, then run `python manage.py migrate` and `python manage.py runserver 0.0.0.0:8000`. For two phones, set `DJANGO_ALLOWED_HOSTS` to the backend host/IP and have both phones use the same reachable base URL. `localhost` on a phone means that phone itself.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/accounts/link/` | Link the verified Firebase identity (created on first authenticated request) |
| GET | `/api/accounts/me/` | Current account |
| GET, PUT, PATCH | `/api/profiles/me/` | Read/create or update own profile |
| POST | `/api/profiles/me/image/` | Upload or replace own profile picture |
| GET, POST | `/api/journeys/` | List/search open journeys or create one as the authenticated driver |
| GET, PUT, PATCH | `/api/journeys/{id}/` | Read or update; only owner may update |
| POST | `/api/journeys/{id}/cancel/` | Cancel own journey |
| POST | `/api/ride-requests/` | Request seats on a journey |
| GET | `/api/ride-requests/mine/` | Passenger's requests and current statuses |
| GET | `/api/ride-requests/journeys/{journey_id}/` | Requests for a journey owned by current driver |
| POST | `/api/ride-requests/{id}/accept/` | Accept pending request (owner only) |
| POST | `/api/ride-requests/{id}/reject/` | Reject pending request (owner only) |
| GET | `/api/matches/` | Matches involving current user |
| GET, POST | `/api/notifications/devices/` | List/register own FCM device token |
| DELETE | `/api/notifications/devices/{id}/` | Remove own device token |
| GET, POST | `/api/reviews/` | List own reviews (or `?user={id}` for reviews of a student) / create a review |
| GET, POST | `/api/reports/` | List own reports / file a report |

Journey search accepts optional `?origin=...&destination=...` substring filters. Journey fields on create: `origin`, `destination`, `departure_time` (ISO 8601), `total_seats`, optional `notes`; available seats are initialized by the server. Example:

```json
{
  "origin": "Patan",
  "destination": "Kirtipur",
  "departure_time": "2026-12-01T08:30:00+05:45",
  "total_seats": 3,
  "notes": "Meet at the main gate"
}
```

Request body: `{ "journey": 12, "seats_requested": 1 }`. Request status is server-controlled (`pending`, `accepted`, `rejected`, `cancelled`). Accepting locks the journey row in a database transaction, decrements seats and creates a match atomically. Rejected requests do not consume seats. A unique journey/passenger constraint prevents duplicate requests.

Profile body fields: `full_name`, `phone_number`, `university`, `student_id`, `is_driver`. Profile responses include `profile_image_url` (empty until an image is uploaded). Token registration body: `{ "token": "FCM registration token", "platform": "android" }`. Review body: `{ "reviewed_user": 4, "journey": 12, "rating": 5, "comment": "On time" }`. Report body: `{ "reported_user": 4, "journey": 12, "description": "..." }`.

## Profile image upload

Send `POST /api/profiles/me/image/` with the Firebase ID token in the Bearer authorization header and a `multipart/form-data` file field named `image`. JPEG, PNG, and WebP image contents are accepted, up to `PROFILE_IMAGE_MAX_BYTES` (5 MiB by default). The server inspects the actual image data, uploads it to Cloudinary over HTTPS, and stores the resulting secure URL and Cloudinary public ID in the authenticated user's MySQL profile row. The public ID is kept server-side for replacement cleanup; API responses expose only the image URL. A user can only upload to their own `/me/` profile.

Example success response:

```json
{
  "success": true,
  "data": {
    "message": "Profile image uploaded successfully",
    "profile_image": "https://res.cloudinary.com/example/image/upload/route/profile_images/example.jpg"
  }
}
```

Flutter example using `http.MultipartRequest`:

```dart
final request = http.MultipartRequest(
  'POST',
  Uri.parse('$baseUrl/api/profiles/me/image/'),
);
request.headers['Authorization'] = 'Bearer $firebaseIdToken';
request.files.add(await http.MultipartFile.fromPath('image', imageFile.path));
final streamed = await request.send();
final response = await http.Response.fromStream(streamed);
final body = jsonDecode(response.body);
if (response.statusCode == 200) {
  final imageUrl = body['data']['profile_image'];
  // Display imageUrl with Image.network(imageUrl).
} else {
  // Validation errors are HTTP 400; missing/invalid auth is 401;
  // Cloudinary upload errors are HTTP 502. Read body['error'] for details.
}
```

When replacing an image, the profile row is updated to the new Cloudinary URL first; the previous Cloudinary asset is then deleted. If old-asset cleanup fails, the new database reference remains valid and the old asset may need later cleanup.

## Phone workflow

1. Each phone signs in with Firebase Auth and sends its current ID token as a Bearer token.
2. Driver registers its FCM token, then POSTs a journey to `/api/journeys/`.
3. Passenger GETs `/api/journeys/`, then POSTs to `/api/ride-requests/`.
4. Django saves request state in MySQL and sends FCM to the driver's registered devices.
5. Driver GETs `/api/ride-requests/journeys/{id}/` and accepts or rejects the request.
6. Passenger GETs `/api/ride-requests/mine/` to see status; both can GET `/api/matches/`.

Push delivery requires a valid Firebase Admin service account path on the Django server and registered device tokens. Ride data stays in MySQL; Firestore is not used by this backend.

## Errors

Validation errors return HTTP 400, ownership violations 403, unknown resources 404, and absent/invalid Firebase credentials or tokens 401. The server refuses requests when Firebase token verification is not configured; development clients should not bypass authentication.
