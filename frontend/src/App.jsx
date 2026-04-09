import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import AuthForm from "./components/AuthForm";
import Chat from "./components/Chat";
import Profile from "./components/Profile";
import { useEffect, useState } from "react";
import { supabase } from "./supabaseClient";

function App() {
  const [session, setSession] = useState(null);
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    const init = async () => {
      const {
        data: { session: currentSession },
      } = await supabase.auth.getSession();
      setSession(currentSession ?? null);
      setAuthReady(true);
    };
    init();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      setSession(currentSession ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (!authReady) {
    return (
      <main className="flex h-screen overflow-hidden items-center justify-center bg-gradient-to-br from-slate-100 via-blue-50 to-indigo-100 p-6">
        <div className="card px-6 py-4 text-sm font-medium text-slate-700">Loading application...</div>
      </main>
    );
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            session ? (
              <Navigate to="/chat" replace />
            ) : (
              <main className="h-screen overflow-hidden bg-gradient-to-br from-slate-100 via-blue-50 to-indigo-100 p-4 md:p-6">
                <AuthForm />
              </main>
            )
          }
        />
        <Route
          path="/chat"
          element={
            session ? (
              <Chat />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        <Route
          path="/profile"
          element={
            session ? (
              <Profile />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
