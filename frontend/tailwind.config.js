/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        /**
         * `ink` is the near-black "chrome" of the app: sidebar, primary
         * buttons, headings and body text. `ink-light` is the warm neutral
         * tint used for subtle fills, borders and table dividers.
         */
        ink: {
          DEFAULT: "#1A1A18",
          dark: "#111110",
          darker: "#0B0B0A",
          light: "#EFEEE9",
        },
        /**
         * The yellow accent.
         *
         * Contrast rule: `gold` (#FFC800) is bright enough that it only
         * works as a *background* on light surfaces — yellow text on white
         * is ~1.6:1 and effectively invisible. So:
         *   - on the dark chrome  -> `text-gold` / `border-gold`   (~12:1)
         *   - on white / canvas   -> `text-gold-dark`              (~4.6:1)
         *   - as a fill anywhere  -> `bg-gold` with `text-ink-darker`
         */
        gold: {
          DEFAULT: "#FFC800",
          // Pale yellow for badge/banner fills. Kept saturated enough to read
          // as yellow — a paler cream renders as manila beige next to the
          // white cards it sits on.
          light: "#FFEFB0",
          // Hover step for yellow fills. Deliberately distinct from `dark`:
          // hovering #FFC800 to a dark yellow reads as olive/disabled rather
          // than as a pressed yellow.
          deep: "#E6B400",
          // Text/icon yellow for light surfaces: 6.1:1 on white, 5.3:1 on
          // `gold-light`.
          dark: "#7A5E00",
        },
        // Page background — a warm off-white so the yellow reads as warm.
        canvas: "#FAFAF7",
        // Status colours, deliberately kept: red for danger, green for
        // success. These carry meaning and aren't part of the brand palette.
        rust: {
          DEFAULT: "#C1440E",
          light: "#FBE9E2",
        },
        mint: {
          DEFAULT: "#1F8A5F",
          light: "#E6F5EE",
        },
        // Muted secondary text, warmed to sit with the yellow.
        slate: {
          DEFAULT: "#403E38",
        },
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgba(20, 20, 16, 0.06), 0 1px 3px 0 rgba(20, 20, 16, 0.08)",
        lift: "0 4px 16px -2px rgba(20, 20, 16, 0.14)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
    },
  },
  plugins: [],
};
