// Tailwind Configuration
tailwind.config = {
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                primary: "#4355c1",
                "background-light": "#f6f6f8",
                "background-dark": "#14151e",
            },
            fontFamily: {
                display: "Lexend",
                sans: ["Inter", "sans-serif"],
            },
            borderRadius: {
                DEFAULT: "0.25rem",
                lg: "0.5rem",
                xl: "0.75rem",
                full: "9999px",
                ios: "1.5rem", // Adding ios rounded for enrolled card
            },
        },
    },
};

// Check for system theme preference
if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.classList.add('dark');
}
