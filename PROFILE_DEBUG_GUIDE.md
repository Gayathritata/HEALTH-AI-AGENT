# Profile Display Troubleshooting Guide

## Issue: Patient Profile Details Not Displayed in Sidebar

### What I Fixed
1. **Profile.jsx Bug** - Was passing `user.id` instead of `access_token` to loadProfile function
2. **Chat.jsx Logging** - Added detailed console logging to help debug profile loading issues
3. **Backend Error Handling** - Made profile endpoint more resilient to missing data

### To Test the Fix:

#### Step 1: Restart Your Backend
```bash
cd e:\HOSPITAL AI AGENT\backend
# Make sure venv is activated, then:
python -m uvicorn app.main:app --reload
```

#### Step 2: Clear Browser Cache
- Open DevTools (F12)
- Go to Application tab
- Clear Local Storage (for localhost:5174)
- Clear Session Storage
- Close and reopen the browser

#### Step 3: Test Registration & Profile Display

1. **Register a new user:**
   - Go to http://localhost:5174
   - Click "Create Account"
   - Fill in:
     - Appointment ID: `TEST123`
     - Full Name: `John Doe`
     - Age: `30`
     - Gender: `Male`
     - Phone: `1234567890` (exactly 10 digits)
     - Address: `123 Main St`
   - Submit

2. **Check the sidebar:** You should see all details in "Patient Application Details" panel

3. **Check console (F12):** Look for console logs showing:
   ```
   Profile loaded: {full_name: "John Doe", appointment_id: "TEST123", ...}
   ```

### If Profile Still Shows "Not available":

#### Check 1: Browser Console
Open DevTools (F12) → Console tab and look for:
- `Profile load error: ...` - API call failed
- `Profile API error: 500 - ...` - Backend returned error
- Check the exact error message

#### Check 2: Backend Logs
Check your terminal running uvicorn for any error messages

#### Check 3: Supabase Configuration
If you see errors about Supabase connection:

1. **Verify .env file exists** and contains:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   ```

2. **Verify profiles table exists** in Supabase:
   - Go to https://supabase.com
   - Navigate to your project
   - In SQL Editor, run:
   ```sql
   CREATE TABLE profiles (
     id UUID PRIMARY KEY,
     appointment_id TEXT,
     full_name TEXT,
     age INTEGER,
     gender TEXT,
     phone TEXT,
     address TEXT,
     email TEXT,
     created_at TIMESTAMP DEFAULT NOW()
   );
   ```

#### Check 4: Direct API Test
Open a new browser tab and test the API directly:

1. **Get an access token:**
   - Login on the main page
   - Open DevTools → Application → Local Storage
   - Find `sb-[project-id]-auth-token` 
   - Copy the `access_token` value

2. **Test the profile endpoint:**
   ```bash
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     http://localhost:8000/api/profile
   ```

   It should return:
   ```json
   {
     "appointment_id": "TEST123",
     "full_name": "John Doe",
     "age": 30,
     "gender": "Male",
     "phone": "1234567890",
     "address": "123 Main St"
   }
   ```

### Still Having Issues?

1. **Check that backend is running:** Visit http://localhost:8000 in browser
   - Should show `{"status":"ok","message":"Health AI Agent backend is running"}`

2. **Check CORS isn't blocking:** 
   - DevTools → Network tab
   - Look for `/api/profile` request
   - Check the Response tab for the data

3. **Restart both services:**
   - Stop backend (Ctrl+C)
   - Stop frontend (Ctrl+C)
   - Restart backend first
   - Then restart frontend: `npm run dev`

4. **Run the test script:**
   ```bash
   cd backend
   python test_supabase.py
   ```
   This will verify your Supabase setup

### Summary of Changes Made:
- **frontend/src/components/Chat.jsx** - Added detailed error logging
- **frontend/src/components/Profile.jsx** - Fixed access_token parameter passing
- **backend/app/main.py** - Added localhost:5174 to CORS allowed origins
- **backend/app/services/** - Made all endpoints more resilient to errors

All profile details entered during registration should now display correctly!
