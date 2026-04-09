import { useEffect, useMemo, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import ChatMessage from "./ChatMessage";
import { supabase } from "../supabaseClient";

const CHAT_API_URL = '/api/chat';
const HISTORY_API_URL = '/api/chat/history';
const PROFILE_API_URL = '/api/profile';

const assistantWelcome =
  "Hi, I am your Health AI Agent. Tell me your symptoms or ask a health question.";

function Chat() {
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { id: crypto.randomUUID(), role: "assistant", text: assistantWelcome }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [authReady, setAuthReady] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const disabled = useMemo(() => !input.trim() || isLoading, [input, isLoading]);

  // 🚀 ✅ INSTANT LOAD FROM CACHE (0 DELAY)
  useEffect(() => {
    const cachedProfile = localStorage.getItem("profile");
    if (cachedProfile) {
      setProfile(JSON.parse(cachedProfile));
    }
  }, []);

  const loadHistory = async (accessToken) => {
    try {
      const res = await fetch(HISTORY_API_URL, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) {
        throw new Error("Could not load history");
      }
      const data = await res.json();

      if (!Array.isArray(data) || data.length === 0) {
        setMessages([{ id: crypto.randomUUID(), role: "assistant", text: assistantWelcome }]);
        return;
      }

      const parsed = [];
      data.forEach((item) => {
        parsed.push({ id: crypto.randomUUID(), role: "user", text: item.user_message });
        parsed.push({ id: crypto.randomUUID(), role: "assistant", text: item.ai_response });
      });
      setMessages(parsed);
    } catch (error) {
      setMessages([{ id: crypto.randomUUID(), role: "assistant", text: assistantWelcome }]);
      console.error(error);
    }
  };

  const loadProfile = async (accessToken, retryCount = 0) => {
    try {
      const res = await fetch(PROFILE_API_URL, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) {
        const errorText = await res.text();
        console.error(`Profile API error: ${res.status} - ${errorText}`);
        throw new Error(`Could not load profile: ${res.status}`);
      }

      const data = await res.json();

      if (data && Object.keys(data).length > 0) {
        setProfile(data);

        // 🚀 ✅ SAVE TO CACHE (for next instant load)
        localStorage.setItem("profile", JSON.stringify(data));

      } else if (retryCount < 3) {
        setTimeout(() => {
          loadProfile(accessToken, retryCount + 1);
        }, 1000);
      } else {
        setProfile({});
      }
    } catch (error) {
      console.error("Profile load error:", error);
      if (retryCount < 3) {
        setTimeout(() => {
          loadProfile(accessToken, retryCount + 1);
        }, 1000);
      } else {
        setProfile({});
      }
    }
  };

  useEffect(() => {
    let mounted = true;
    let initialLoadDone = false;

    const handleSession = (currentSession) => {
      if (!mounted) return;

      setSession(currentSession ?? null);
      setAuthReady(true);

      if (currentSession?.access_token) {
        if (!initialLoadDone) {
          initialLoadDone = true;

          loadProfile(currentSession.access_token);
          loadHistory(currentSession.access_token);
        }
      } else {
        initialLoadDone = false;
        setProfile(null);
        setMessages([{ id: crypto.randomUUID(), role: "assistant", text: assistantWelcome }]);
        navigate("/");
      }
    };

    supabase.auth.getSession().then(({ data: { session: currentSession } }) => {
      handleSession(currentSession);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, currentSession) => {
      handleSession(currentSession);
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [navigate]);

  const sendMessage = async () => {
    const userText = input.trim();
    if (!userText || !session?.access_token) return;

    const userMessage = { id: crypto.randomUUID(), role: "user", text: userText };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch(CHAT_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ message: userText }),
      });

      if (!res.ok) {
        throw new Error("Failed to get response from backend");
      }

      const data = await res.json();
      const aiMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: data.ai_response,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: "Sorry, I could not connect to the backend. Please check if the server is running.",
        },
      ]);
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      sendMessage();
    }
  };

  const handleLogout = async () => {
    localStorage.removeItem("profile"); // clear cache
    await supabase.auth.signOut();
  };

  if (!authReady) {
    return (
      <main className="flex h-screen overflow-hidden items-center justify-center bg-gradient-to-br from-slate-100 via-blue-50 to-indigo-100 p-6">
        <div className="card px-6 py-4 text-sm font-medium text-slate-700">Loading application...</div>
      </main>
    );
  }

  return (
    <main className="h-screen overflow-hidden bg-gradient-to-br from-slate-100 via-blue-50 to-indigo-100 p-3 md:p-4">
      <div className="mx-auto flex h-full w-full max-w-4xl flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white/85 shadow-2xl shadow-slate-300/40 backdrop-blur">

        {/* --- YOUR UI UNCHANGED --- */}

        <header className="bg-gradient-to-r from-blue-700 via-blue-600 to-indigo-600 px-4 py-3 text-white">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h1 className="text-xl font-semibold tracking-tight">Health AI Agent</h1>
              <p className="text-xs text-blue-100">Symptom checker and smart health guidance</p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                className="rounded-xl bg-white px-3.5 py-1.5 text-xs font-semibold text-blue-700 shadow-sm transition hover:bg-blue-50"
                onClick={() => {
                  navigate("/profile", { state: { profile } });
                }}
              >
                View Profile
              </button>
              <button onClick={handleLogout} className="rounded-xl bg-white px-3.5 py-1.5 text-xs font-semibold text-blue-700">
                Logout
              </button>
            </div>
          </div>
        </header>

        <div className="grid flex-1 min-h-0 gap-5 p-5 md:grid-cols-[340px_1fr]">

          <aside className="card p-5">
            <h2 className="text-base font-semibold text-slate-800">Patient Application Details</h2>
            <div className="mt-3 space-y-2 text-xs text-slate-700">
              <p><span className="font-medium">Full name:</span> {profile?.full_name || "Not available"}</p>
              <p><span className="font-medium">Appointment ID:</span> {profile?.appointment_id || "Not available"}</p>
              <p><span className="font-medium">Age:</span> {profile?.age ?? "Not available"}</p>
              <p><span className="font-medium">Gender:</span> {profile?.gender || "Not available"}</p>
              <p><span className="font-medium">Phone:</span> {profile?.phone || "Not available"}</p>
              <p><span className="font-medium">Address:</span> {profile?.address || "Not available"}</p>
            </div>
          </aside>

          {/* Chat section unchanged */}
          <section className="card flex flex-col overflow-hidden min-h-0">
            <div className="flex-1 overflow-y-auto p-5">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} role={msg.role} text={msg.text} />
              ))}
              <div ref={messagesEndRef} />
            </div>

            <div className="border-t p-3 flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="input-field flex-1"
              />
              <button onClick={sendMessage} className="btn-primary">
                {isLoading ? "..." : "Send"}
              </button>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

export default Chat;