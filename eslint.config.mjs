import css from "@eslint/css";
import { defineConfig } from "eslint/config";

export default defineConfig([
	{
        files: ["**/*.css"],
        plugins: {
            css,
        },
        extends: ["css/recommended"],
        language: "css/css",
    },
]);
