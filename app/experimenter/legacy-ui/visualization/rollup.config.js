import commonjs from "@rollup/plugin-commonjs";
import resolve from "@rollup/plugin-node-resolve";
import typescript from "@rollup/plugin-typescript";
import copy from "rollup-plugin-copy";
import livereload from "rollup-plugin-livereload";
import postcss from "rollup-plugin-postcss";
import svelte from "rollup-plugin-svelte";
import { terser } from "rollup-plugin-terser";
import sveltePreprocess from "svelte-preprocess";
import css from "rollup-plugin-css-only";

const production = !process.env.ROLLUP_WATCH;

export default [
  {
    input: "src/main.js",
    output: {
      sourcemap: true,
      format: "iife",
      name: "app",
      file: "../assets/visualization/bundle.js",
    },
    plugins: [
      postcss(),
      copy({
        targets: [
          { src: "public/global.css", dest: "../assets/visualization/" },
        ],
      }),
      svelte({
        compilerOptions: {
          // enable run-time checks when not in production
          dev: !production,
        },
        preprocess: sveltePreprocess(),
      }),
      // we'll extract any component CSS out into
      // a separate file - better for performance
      css({ output: "bundle.css" }),

      typescript({ sourceMap: !production }),

      // If you have external dependencies installed from
      // npm, you'll most likely need these plugins. In
      // some cases you'll need additional configuration -
      // consult the documentation for details:
      // https://github.com/rollup/plugins/tree/master/packages/commonjs
      resolve({
        jsnext: true,
        browser: true,
        dedupe: ["svelte"],
      }),
      commonjs(),

      // Watch the `public` directory and refresh the
      // browser on changes when not in production
      !production && livereload("public"),

      // If we're building for production (npm run build
      // instead of npm run dev), minify
      production && terser(),
    ],
    watch: {
      clearScreen: false,
    },
  },
];
