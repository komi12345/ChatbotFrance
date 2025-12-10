import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    screens: {
      'xs': '375px',
      'sm': '640px',
      'md': '768px',
      'lg': '1024px',
      'xl': '1280px',
      '2xl': '1536px',
    },
    extend: {
      colors: {
        // Couleurs principales
        emerald: {
          DEFAULT: "#10B981",
          50: "#D1FAE5",
          100: "#A7F3D0",
          200: "#6EE7B7",
          300: "#34D399",
          400: "#10B981",
          500: "#059669",
          600: "#047857",
          700: "#065F46",
          800: "#064E3B",
          900: "#022C22",
        },
        // Sidebar
        sidebar: {
          DEFAULT: "#1F2937",
          dark: "#2C3E50",
        },
        // Couleurs de statut
        status: {
          success: "#10B981",
          error: "#EF4444",
          warning: "#F59E0B",
          pending: "#F59E0B",
        },
        // Textes
        text: {
          primary: "#111827",
          secondary: "#6B7280",
          muted: "#9CA3AF",
        },
        // Fonds
        surface: {
          DEFAULT: "#F9FAFB",
          card: "#FFFFFF",
          hover: "#F3F4F6",
        },
        // Bordures
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        xl: "12px",
        "2xl": "16px",
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0, 0, 0, 0.1)',
        'card-hover': '0 4px 6px rgba(0, 0, 0, 0.1)',
        'soft': '0 1px 3px rgba(0, 0, 0, 0.08)',
        'login': '0 10px 40px rgba(0, 0, 0, 0.1)',
      },
      backgroundImage: {
        // Dégradés pour les cartes de catégories
        'gradient-1': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'gradient-2': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'gradient-3': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'gradient-4': 'linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%)',
        'gradient-5': 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
        'gradient-6': 'linear-gradient(135deg, #2c3e50 0%, #3498db 100%)',
        'gradient-red-yellow': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        // Dégradé pour la page de login
        'gradient-login': 'linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%)',
        'gradient-login-decoration': 'linear-gradient(135deg, #a7f3d0 0%, #6ee7b7 50%, #5eead4 100%)',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [],
};

export default config;
