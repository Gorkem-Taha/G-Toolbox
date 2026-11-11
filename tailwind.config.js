/** Tailwind config for the offline build (replaces the cdn.tailwindcss.com runtime). */
module.exports = {
  content: ["./templates/**/*.html", "./static/js/**/*.js"],
  theme: { extend: {} },
  plugins: [],
};
