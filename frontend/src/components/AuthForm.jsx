import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../supabaseClient";

function AuthForm() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [fullName, setFullName] = useState("");
  const [appointmentId, setAppointmentId] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("error");
  const [isLoading, setIsLoading] = useState(false);

  const buildLoginEmail = (idValue) => {
    const normalized = idValue
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]/g, "");
    const safeLocalPart = normalized || "patient";
    return `${safeLocalPart}@hospital.com`;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage("");
    setIsLoading(true);

    try {
      const authEmail = buildLoginEmail(appointmentId);
      if (!appointmentId.trim()) {
        throw new Error("Appointment ID is required.");
      }

      // Phone validation for registration
      if (!isLogin) {
        if (phone.length !== 10) {
          throw new Error("Phone number must be exactly 10 digits.");
        }
        if (!address.trim()) {
          throw new Error("Address is required.");
        }
      }

      const defaultPassword = "defaultpassword123"; // Default password for all users

      if (isLogin) {
        const { error } = await supabase.auth.signInWithPassword({ email: authEmail, password: defaultPassword });
        if (error) throw error;
        setMessageType("success");
        setMessage("Login successful! Redirecting to chat...");
        setTimeout(() => navigate("/chat"), 800);
      } else {
        const { data, error } = await supabase.auth.signUp({ email: authEmail, password: defaultPassword });
        if (error) throw error;

        const userId = data.user?.id;
        if (userId) {
          const { error: profileError } = await supabase.from("profiles").upsert({
            id: userId,
            appointment_id: appointmentId.trim(),
            full_name: fullName.trim() || null,
            age: age ? Number(age) : null,
            gender: gender.trim() || null,
            phone: phone.trim() || null,
            address: address.trim() || null,
            email: authEmail,
          });
          if (profileError) throw profileError;
        }

        // Auto-login after registration so user directly lands on chat page.
        const { error: signInError } = await supabase.auth.signInWithPassword({
          email: authEmail,
          password: defaultPassword,
        });
        if (signInError) {
          throw new Error(
            "Registered successfully, but auto-login failed. Please login manually once."
          );
        }

        setMessageType("success");
        setMessage("Registration successful! Redirecting to chat...");
        setTimeout(() => navigate("/chat"), 800);
      }
    } catch (error) {
      const rawMessage = String(error?.message || "Authentication failed.");
      const lowerMessage = rawMessage.toLowerCase();
      setMessageType("error");

      if (lowerMessage.includes("email rate limit exceeded") || lowerMessage.includes("429")) {
        setMessage("Too many attempts right now. Please wait 2-5 minutes, then try again.");
      } else if (lowerMessage.includes("already registered") || lowerMessage.includes("user already registered")) {
        setIsLogin(true);
        setMessage("This appointment ID already exists. Please login with your appointment ID.");
      } else if (lowerMessage.includes("invalid login credentials")) {
        setMessage("Invalid appointment ID. Please check and try again.");
      } else {
        setMessage(rawMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto h-full w-full max-w-4xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl shadow-slate-300/30">
      <div className="grid h-full md:grid-cols-2">
        <section
          className="relative hidden md:block"
          style={{
            backgroundImage:
              "url('https://images.unsplash.com/photo-1631217868264-e5b90bb7e133?auto=format&fit=crop&w=1200&q=80')",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-blue-900/75 via-blue-800/60 to-indigo-900/65" />
          <div className="relative z-10 flex h-full flex-col justify-end p-6 text-white">
            <p className="mb-2 inline-flex w-fit rounded-full border border-white/30 bg-white/10 px-2 py-1 text-[10px] font-semibold">
              Patient Support Platform
            </p>
            <h2 className="text-2xl font-bold leading-tight">Hospital Care Portal</h2>
            <p className="mt-1.5 max-w-sm text-[11px] leading-relaxed text-blue-100">
              Describe symptoms, review profile details, and receive guided first-step health
              suggestions.
            </p>
          </div>
        </section>

        <section className="flex items-center justify-center overflow-hidden bg-white p-2 md:p-4">
          <div className="w-full max-w-sm">
            <p className="inline-flex rounded-full bg-blue-50 px-2.5 py-1 text-[10px] font-semibold text-blue-700">
              Secure Patient Portal
            </p>
            <h1 className="mt-0.5 text-lg font-bold text-slate-800">{isLogin ? "Welcome Back" : "Create Account"}</h1>

            <form className="mt-2 space-y-1.5" onSubmit={handleSubmit}>
              {!isLogin ? (
                <div className="grid grid-cols-2 gap-1.5">
                  <input
                    type="text"
                    placeholder="Appointment ID"
                    className="input-field col-span-2"
                    value={appointmentId}
                    onChange={(e) => setAppointmentId(e.target.value)}
                    required
                  />
                  <input
                    type="text"
                    placeholder="Full name"
                    className="input-field col-span-2"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                  />
                  <input
                    type="number"
                    min="1"
                    placeholder="Age"
                    className="input-field"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    required
                  />
                  <select
                    className="input-field"
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    required
                  >
                    <option value="">Select Gender</option>
                    <option value="MALE">Male</option>
                    <option value="FEMALE">Female</option>
                  </select>
                  <input
                    type="tel"
                    placeholder="Phone number (10 digits)"
                    className="input-field col-span-2"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value.replace(/[^0-9]/g, '').slice(0, 10))}
                    maxLength="10"
                    required
                  />
                  <textarea
                    placeholder="Address"
                    className="input-field col-span-2 resize-none"
                    rows={2}
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    required
                  />
                </div>
              ) : (
                <>
                  <input
                    type="text"
                    placeholder="Appointment ID"
                    className="input-field"
                    value={appointmentId}
                    onChange={(e) => setAppointmentId(e.target.value)}
                    required
                  />
                </>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full"
              >
                {isLoading ? "Please wait..." : isLogin ? "Login" : "Register"}
              </button>
            </form>

            <button
              type="button"
              className="mt-1.5 text-xs font-medium text-blue-700 hover:text-blue-800"
              onClick={() => {
                setIsLogin((prev) => !prev);
                setMessage("");
                setAppointmentId("");
                setFullName("");
                setAge("");
                setGender("");
                setPhone("");
                setAddress("");
              }}
            >
              {isLogin ? "New user? Register here" : "Already have an account? Login"}
            </button>

            {message && (
              <p
                className={`mt-1 rounded-xl px-3 py-1.5 text-xs transition ${
                  messageType === "success"
                    ? "border border-emerald-200 bg-emerald-50 text-emerald-700"
                    : "border border-slate-200 bg-slate-50 text-slate-700"
                }`}
              >
                {message}
              </p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

export default AuthForm;
