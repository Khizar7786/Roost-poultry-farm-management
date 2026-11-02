import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import * as authApi from "../api/auth";
import { setTokens, clearTokens } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);

  const refreshUser = useCallback(async () => {
    const access = localStorage.getItem("roost_access");
    if (!access) {
      setUser(null);
      setInitializing(false);
      return;
    }
    try {
      const me = await authApi.getMe();
      setUser(me);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setInitializing(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (username, password) => {
    const data = await authApi.login(username, password);
    setTokens({ access: data.access, refresh: data.refresh });
    const me = await authApi.getMe();
    setUser(me);
    return me;
  };

  const register = async (payload) => {
    return authApi.registerFarm(payload);
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, initializing, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
