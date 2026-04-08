# Health AI Agent

A beginner-friendly full-stack AI project with:

- Frontend: React (Vite) + Tailwind CSS
- Backend: FastAPI
- AI workflow: LangGraph (agentic decision flow)
- Database + Auth: Supabase (user auth + chat history)

## Project Structure

```text
Health AI Agent/
  frontend/                 # React + Vite + Tailwind app + Supabase Auth
  backend/                  # FastAPI + LangGraph + Supabase integration
    app/
      main.py
      routers/
      services/
      models/
```

## Features

- Login and registration pages (Supabase Auth)
- Existing users can log in directly
- Chat UI with message bubbles, input box, and send button
- Symptom checker (fever, cold, headache, etc.)
- Basic health suggestions for common issues
- Escalation suggestion for serious symptoms
- Per-user chat history storage in Supabase
- Clean modular backend structure with routers/services/models

## Supabase Setup (Auth + Database)

1. Create a Supabase project.
2. In **Authentication**, keep Email auth enabled.
3. In **SQL Editor**, run:

   ```sql
   create table if not exists public.chat_history (
     id bigint generated always as identity primary key,
     user_id uuid not null references auth.users(id) on delete cascade,
     user_message text not null,
     ai_response text not null,
     response_type text not null,
     created_at timestamp with time zone default timezone('utc', now())
   );

   create index if not exists idx_chat_history_user_id_created_at
   on public.chat_history(user_id, created_at);

   create table if not exists public.profiles (
     id uuid primary key references auth.users(id) on delete cascade,
     appointment_id text unique,
     full_name text,
     email text,
     age int,
     gender text,
     phone text,
     created_at timestamp with time zone default timezone('utc', now())
   );

   alter table public.profiles enable row level security;

   create policy "Users can insert own profile"
   on public.profiles
   for insert
   to authenticated
   with check (auth.uid() = id);

   create policy "Users can update own profile"
   on public.profiles
   for update
   to authenticated
   using (auth.uid() = id)
   with check (auth.uid() = id);

   create policy "Users can view own profile"
   on public.profiles
   for select
   to authenticated
   using (auth.uid() = id);

   -- If profiles table already existed, ensure these columns are present:
   alter table public.profiles add column if not exists appointment_id text;
   alter table public.profiles add column if not exists age int;
   alter table public.profiles add column if not exists gender text;
   alter table public.profiles add column if not exists phone text;
   create unique index if not exists idx_profiles_appointment_id on public.profiles(appointment_id);
   ```

4. From **Settings -> API**, copy:
   - Project URL
   - anon key (for frontend)
   - service_role key (for backend)

## Backend Setup (FastAPI + LangGraph)

1. Open terminal in `backend/`.
2. Create and activate virtual environment:

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure backend env:

   - Copy `backend/.env.example` to `backend/.env`
   - Set:
     - `SUPABASE_URL`
     - `SUPABASE_KEY` (use `service_role` key for backend)

5. Run backend:

   ```bash
   uvicorn app.main:app --reload
   ```

Backend runs at `http://127.0.0.1:8000`

## Frontend Setup (React + Vite + Tailwind)

1. Open terminal in `frontend/`.
2. Install dependencies:

   ```bash
   npm install
   ```

3. Configure frontend env:

   - Copy `frontend/.env.example` to `frontend/.env`
   - Set:
     - `VITE_SUPABASE_URL`
     - `VITE_SUPABASE_ANON_KEY`
     - `VITE_BACKEND_URL` (default `http://127.0.0.1:8000`)

4. Run frontend:

   ```bash
   npm run dev
   ```

Frontend runs at `http://localhost:5173`

## API Endpoints

### POST `/api/chat`

- Requires `Authorization: Bearer <supabase_access_token>`
- Request body:

```json
{
  "message": "I have fever and headache"
}
```

- Response body:

```json
{
  "user_message": "I have fever and headache",
  "ai_response": "Thanks for sharing: 'I have fever and headache'. This seems like a common health concern...",
  "response_type": "common_issue"
}
```

### GET `/api/chat/history`

- Requires `Authorization: Bearer <supabase_access_token>`
- Returns logged-in user's chat history

## How the LangGraph Agent Works

The workflow in `backend/app/services/agent.py`:

1. Analyze user input
2. Decide response type using symptom keywords
3. Generate final response

## Notes

- This project provides general health guidance and is not a medical diagnosis tool.
- For severe or worsening symptoms, users should consult a licensed medical professional.
