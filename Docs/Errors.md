Fix these two bugs:

1. Create .env.local in /frontend with:
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
Then make sure all Axios calls use this env variable as base URL.

2. In /frontend/src/app/layout.tsx, change:
<html lang="en">
to:
<html lang="en" suppressHydrationWarning>