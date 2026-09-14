import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { AnimatedBackground } from "../components/core/AnimatedBackground";
import { AIAvatar } from "../components/core/AIAvatar";
import { useAuthStore } from "../store/authStore";

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);
  
  // Login State
  const [loginName, setLoginName] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState("");

  // Signup State
  const [signupName, setSignupName] = useState("");
  const [signupEmail, setSignupEmail] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [signupConfirmPassword, setSignupConfirmPassword] = useState("");
  const [signupDob, setSignupDob] = useState("");
  const [signupError, setSignupError] = useState("");

  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const signup = useAuthStore((state) => state.signup);
  const currentUser = useAuthStore((state) => state.currentUser);

  useEffect(() => {
    if (currentUser) {
      navigate("/", { replace: true });
    }
  }, [currentUser, navigate]);

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    setLoginError("");
    
    const success = login(loginName.trim(), loginPassword);
    if (success) {
      navigate("/");
    } else {
      setLoginError("Invalid User Name or Password. Did you sign up first?");
    }
  };

  const handleSignupSubmit = (e) => {
    e.preventDefault();
    setSignupError("");

    if (signupPassword !== signupConfirmPassword) {
      setSignupError("Passwords do not match");
      return;
    }

    // Save to mock frontend store
    signup({
      name: signupName.trim(),
      email: signupEmail.trim(),
      password: signupPassword,
      dob: signupDob
    });

    // Reset signup form and switch to login
    setSignupName("");
    setSignupEmail("");
    setSignupPassword("");
    setSignupConfirmPassword("");
    setSignupDob("");
    
    setIsLogin(true);
  };

  const toggleAuthMode = () => {
    setIsLogin((prev) => !prev);
    setLoginError("");
    setSignupError("");
  };

  return (
    <div className="relative h-screen bg-canvas flex flex-col items-center justify-center overflow-hidden">
      <AnimatedBackground />

      <div className="z-10 w-full max-w-md px-4">
        <div className="flex justify-center mb-8">
          <AIAvatar size="medium" state="idle" />
        </div>

        <div className="relative w-full overflow-hidden rounded-3xl">
          <AnimatePresence mode="wait">
            {isLogin ? (
              <motion.div
                key="login"
                initial={{ opacity: 0, x: -50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 50 }}
                transition={{ duration: 0.4, ease: "easeInOut" }}
                className="w-full glass-panel p-8 flex flex-col justify-center rounded-3xl"
              >
                <h2 className="text-3xl font-medium text-text-primary mb-2 text-center">Welcome Back</h2>
                <p className="text-text-secondary text-center mb-8">Continue your journey with AURA</p>

                <form onSubmit={handleLoginSubmit} className="flex flex-col gap-4">
                  {loginError && (
                    <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm text-center">
                      {loginError}
                    </div>
                  )}
                  <div>
                    <input
                      type="text"
                      placeholder="User Name"
                      required
                      value={loginName}
                      onChange={(e) => setLoginName(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-border bg-surface-soft text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary/50 transition-all"
                    />
                  </div>
                  <div>
                    <input
                      type="password"
                      placeholder="Password"
                      required
                      value={loginPassword}
                      onChange={(e) => setLoginPassword(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-border bg-surface-soft text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary/50 transition-all"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full mt-4 py-3 rounded-xl bg-accent-primary hover:bg-accent-secondary text-white font-medium transition-colors shadow-soft hover:shadow-float flex justify-center items-center gap-2"
                  >
                    Access Workspace
                  </button>
                </form>

                <div className="mt-8 text-center text-text-secondary text-sm">
                  Don't have an account?{" "}
                  <button
                    type="button"
                    onClick={toggleAuthMode}
                    className="text-accent-primary font-medium hover:underline"
                  >
                    Sign Up
                  </button>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="signup"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ duration: 0.4, ease: "easeInOut" }}
                className="w-full glass-panel p-8 flex flex-col justify-center rounded-3xl"
              >
                <h2 className="text-3xl font-medium text-text-primary mb-2 text-center">Join AURA</h2>
                <p className="text-text-secondary text-center mb-8">Experience the future of AI</p>

                <form onSubmit={handleSignupSubmit} className="flex flex-col gap-4">
                  {signupError && (
                    <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm text-center">
                      {signupError}
                    </div>
                  )}
                  <div>
                    <input
                      type="text"
                      placeholder="Name"
                      required
                      value={signupName}
                      onChange={(e) => setSignupName(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-border bg-surface-soft text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary/50 transition-all"
                    />
                  </div>
                  <div>
                    <input
                      type="email"
                      placeholder="Email Address"
                      required
                      value={signupEmail}
                      onChange={(e) => setSignupEmail(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-border bg-surface-soft text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary/50 transition-all"
                    />
                  </div>
                  <div>
                    <input
                      type="date"
                      required
                      value={signupDob}
                      onChange={(e) => setSignupDob(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-border bg-surface-soft text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary/50 transition-all"
                    />
                  </div>
                  <div>
                    <input
                      type="password"
                      placeholder="Password"
                      required
                      value={signupPassword}
                      onChange={(e) => setSignupPassword(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-border bg-surface-soft text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary/50 transition-all"
                    />
                  </div>
                  <div>
                    <input
                      type="password"
                      placeholder="Confirm Password"
                      required
                      value={signupConfirmPassword}
                      onChange={(e) => setSignupConfirmPassword(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-border bg-surface-soft text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary/50 transition-all"
                    />
                  </div>
                  
                  <button
                    type="submit"
                    className="w-full mt-4 py-3 rounded-xl bg-accent-primary hover:bg-accent-secondary text-white font-medium transition-colors shadow-soft hover:shadow-float flex justify-center items-center gap-2"
                  >
                    Create Account
                  </button>
                </form>

                <div className="mt-8 text-center text-text-secondary text-sm">
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={toggleAuthMode}
                    className="text-accent-primary font-medium hover:underline"
                  >
                    Login
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
