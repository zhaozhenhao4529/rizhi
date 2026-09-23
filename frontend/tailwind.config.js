/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        cream: '#FAF6EF',
        card: '#FFFFFF',
        ink: '#2B2622',
        soft: '#8A8378',
        accent: '#C96F4A',
        'accent-dark': '#A85436',
        sage: '#8A9B7E',
        sand: '#EFE8DC',
      },
      fontFamily: {
        display: ['"Songti SC"', '"Noto Serif CJK SC"', '"Source Han Serif SC"', '"SimSun"', 'serif'],
        body: ['"PingFang SC"', '"Noto Sans SC"', '"Source Han Sans SC"', '"Microsoft YaHei"', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 4px 20px rgba(43, 38, 34, 0.08)',
        lift: '0 8px 30px rgba(43, 38, 34, 0.14)',
      },
    },
  },
  plugins: [],
}
