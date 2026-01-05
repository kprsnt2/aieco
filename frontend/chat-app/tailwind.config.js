/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
            colors: {
                primary: {
                    50: '#eef2ff',
                    100: '#e0e7ff',
                    500: '#667eea',
                    600: '#5a67d8',
                    700: '#4c51bf',
                },
            },
            animation: {
                'fade-in': 'fadeIn 0.3s ease-out forwards',
            },
        },
    },
    plugins: [],
}
