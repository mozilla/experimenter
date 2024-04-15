import { nodeResolve } from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import terser from "@rollup/plugin-terser";

export default {
  input: "./src/index.js",
  output: {
    file: "../../static/scripts/bundle.js",
    format: "iife",
  },
  plugins: [
    nodeResolve(),
    commonjs({
      include: "node_modules/**",
    }),
    terser(),
  ],
};
