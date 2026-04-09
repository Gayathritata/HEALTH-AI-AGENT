import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { supabase } from "../supabaseClient";

const PROFILE_API_URL = '/api/profile';
const HISTORY_API_URL = '/api/chat/history';

function Profile() {
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const location = useLocation();

  const [profile, setProfile] = useState(
    location.state?.profile || JSON.parse(localStorage.getItem("profile") || "null")
  );
  const [history, setHistory] = useState([]);
  const [authReady, setAuthReady] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedProfile, setEditedProfile] = useState({});

  const loadProfile = async (accessToken) => {
    try {
      const res = await fetch(PROFILE_API_URL, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) throw new Error("Could not load profile");
      const data = await res.json();
      setProfile(data);
      setEditedProfile(data);
      localStorage.setItem("profile", JSON.stringify(data));
    } catch (error) {
      console.error(error);
    }
  };

  const loadHistory = async (accessToken) => {
    try {
      const res = await fetch(HISTORY_API_URL, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) throw new Error("Could not load history");
      const data = await res.json();
      setHistory(data.slice(-5)); // Last 5 interactions
    } catch (error) {
      console.error(error);
    }
  };

  const saveProfile = async () => {
    if (!session?.user?.id) return;
    try {
      const { error } = await supabase
        .from("profiles")
        .upsert({
          id: session.user.id,
          full_name: editedProfile.full_name,
          age: editedProfile.age,
          gender: editedProfile.gender,
          phone: editedProfile.phone,
          address: editedProfile.address,
        });
      if (error) throw error;
      setProfile(editedProfile);
      setIsEditing(false);
      alert("Profile updated successfully!");
    } catch (error) {
      console.error(error);
      alert("Failed to update profile.");
    }
  };

  useEffect(() => {
    const init = async () => {
      const {
        data: { session: currentSession },
      } = await supabase.auth.getSession();

      if (!currentSession) {
        navigate("/");
        return;
      }

      setSession(currentSession);
      setAuthReady(true);
      if (currentSession?.access_token) {
        loadProfile(currentSession.access_token);
        loadHistory(currentSession.access_token);
      }
    };
    init();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      setSession(currentSession);
      if (currentSession?.access_token) {
        loadProfile(currentSession.access_token);
        loadHistory(currentSession.access_token);
      } else {
        navigate("/");
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  if (!authReady) {
    return (
      <main className="flex h-screen overflow-hidden items-center justify-center bg-gradient-to-br from-slate-100 via-blue-50 to-indigo-100 p-6">
        <div className="card px-6 py-4 text-sm font-medium text-slate-700">Loading profile...</div>
      </main>
    );
  }

  return (
    <main className="h-screen overflow-hidden bg-gradient-to-br from-slate-100 via-blue-50 to-indigo-100 p-3 md:p-4">
      <div className="mx-auto h-full w-full max-w-2xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl shadow-slate-300/30">
        <div className="flex h-full flex-col">
          <header className="flex items-center justify-between border-b border-slate-200 px-3 py-2">
            <h1 className="text-lg font-semibold text-slate-800">Patient Profile</h1>
            <div className="flex gap-2">
              {isEditing ? (
                <>
                  <button
                    onClick={saveProfile}
                    className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
                  >
                    Save Changes
                  </button>
                  <button
                    onClick={() => {
                      setIsEditing(false);
                      setEditedProfile(profile);
                    }}
                    className="rounded-lg bg-gray-600 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Edit Profile
                </button>
              )}
              <button
                onClick={() => navigate("/chat")}
                className="rounded-lg bg-gray-600 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
              >
                Back to Chat
              </button>
            </div>
          </header>
          <div className="flex-1 overflow-y-auto p-3">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h2 className="mb-3 text-base font-medium text-slate-800">Personal Details</h2>
                <div className="space-y-2">
                  <div>
                    <label className="text-sm font-medium text-slate-600">Appointment ID</label>
                    <p className="text-sm text-slate-800">{profile?.appointment_id || "N/A"}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-600">Full Name</label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={editedProfile.full_name || ""}
                        onChange={(e) => setEditedProfile({ ...editedProfile, full_name: e.target.value })}
                        className="input-field"
                      />
                    ) : (
                      <p className="text-sm text-slate-800">{profile?.full_name || "N/A"}</p>
                    )}
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-600">Age</label>
                    {isEditing ? (
                      <input
                        type="number"
                        value={editedProfile.age || ""}
                        onChange={(e) => setEditedProfile({ ...editedProfile, age: e.target.value ? Number(e.target.value) : null })}
                        className="input-field"
                      />
                    ) : (
                      <p className="text-sm text-slate-800">{profile?.age ?? "N/A"}</p>
                    )}
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-600">Gender</label>
                    {isEditing ? (
                      <select
                        value={editedProfile.gender || ""}
                        onChange={(e) => setEditedProfile({ ...editedProfile, gender: e.target.value })}
                        className="input-field"
                      >
                        <option value="">Select Gender</option>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                      </select>
                    ) : (
                      <p className="text-sm text-slate-800">{profile?.gender || "N/A"}</p>
                    )}
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-600">Phone</label>
                    {isEditing ? (
                      <input
                        type="tel"
                        value={editedProfile.phone || ""}
                        onChange={(e) => setEditedProfile({ ...editedProfile, phone: e.target.value.replace(/[^0-9]/g, '').slice(0, 10) })}
                        maxLength="10"
                        className="input-field"
                      />
                    ) : (
                      <p className="text-sm text-slate-800">{profile?.phone || "N/A"}</p>
                    )}
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-600">Address</label>
                    {isEditing ? (
                      <textarea
                        value={editedProfile.address || ""}
                        onChange={(e) => setEditedProfile({ ...editedProfile, address: e.target.value })}
                        rows="1.5"
                        className="input-field resize-none"
                      />
                    ) : (
                      <p className="text-sm text-slate-800">{profile?.address || "N/A"}</p>
                    )}
                  </div>
                </div>
              </div>
              <div>
                <h2 className="mb-3 text-base font-medium text-slate-800">Recent Health Interactions</h2>
                <div className="space-y-2">
                  {history.length > 0 ? (
                    history.map((item, index) => (
                      <div key={index} className="rounded-lg border border-slate-200 p-3">
                        <p className="text-xs text-slate-600">{new Date(item.created_at).toLocaleDateString()}</p>
                        <p className="text-sm text-slate-800"><strong>You:</strong> {item.user_message}</p>
                        <p className="text-sm text-slate-800"><strong>AI:</strong> {item.ai_response}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-600">No recent interactions.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

export default Profile;