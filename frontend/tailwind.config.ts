import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#10131A',
          900: '#141922',
          800: '#1B2130',
          700: '#252D3F',
        },
        paper: {
          50: '#FAF7F0',
          100: '#F4EFE4',
          200: '#E8E0CE',
          300: '#D6CCA8',
        },
        brass: {
          300: '#E0B979',
          400: '#D3A459',
          500: '#C4903F',
          600: '#A6732B',
        },
        signal: {
          teal: '#3E8E82',
          rust: '#B4482E',
          amber: '#D9A441',
        },
      },
      fontFamily: {
        display: ['Fraunces', 'serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      backgroundImage: {
        'grid-pattern': 'radial-gradient(rgba(196, 144, 63, 0.12) 1px, transparent 1px)',
        'blueprint': 'linear-gradient(to right, rgba(196, 144, 63, 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(196, 144, 63, 0.05) 1px, transparent 1px)',
      },
      boxShadow: {
        'brass-glow': '0 0 15px rgba(196, 144, 63, 0.25)',
        'brass-sm': '0 0 8px rgba(196, 144, 63, 0.15)',
        'instrument': 'inset 0 1px 2px rgba(255, 255, 255, 0.05), 0 4px 12px rgba(0, 0, 0, 0.5)',
      },
    },
  },
  plugins: [],
};

export default config;
