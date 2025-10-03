import { defineStore } from "pinia";
import axios from "axios";

const api = axios.create({
    baseURL: `${import.meta.env.VITE_BACKEND_URL}`,
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
    }
});

export const useAuthStore = defineStore("auth",
    {
        state: () => ({
            user: null,
            isAuthenticated: false,
            loading: true
        }),
        actions: {
            async fetchUser() {
                this.loading = true;
                try {
                    const res = await api.get("/auth/user");
                    console.log("sasa" + res.data.username);

                    if (res.data.isAuthenticated) {
                        this.user = res.data.username;
                        this.isAuthenticated = true;
                    }
                    else {
                        this.user = null;
                        this.isAuthenticated = false;
                    }

                } catch (error) {
                    this.user = null;
                    this.isAuthenticated = false;
                }
                finally {
                    this.loading = false;
                }
            },

            async login() {
                window.location.href = `${import.meta.env.VITE_BACKEND_URL}/auth/login`;
            },

            async logout() {
                this.loading = true;
                try {
                    // Use the pre-configured axios instance for consistency
                    await api.get(`/auth/logout`);
                } catch (error) {
                    console.error("Logout request failed, but proceeding with client-side logout.", error);
                } finally {
                    // This block will run regardless of whether the API call succeeded or failed
                    this.user = null;
                    this.isAuthenticated = false;
                    this.loading = false;
                }
            }
        }
    }
);