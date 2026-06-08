import type { ZudokuConfig } from "zudoku";
import { endpointNavigation } from "./endpoint-navigation";

/**
 * Developer Portal Configuration
 * For more information, see:
 * https://zuplo.com/docs/dev-portal/zudoku/configuration/overview
 */
const config: ZudokuConfig = {
	site: {
		title: "VerifyAfrica Docs",
		logo: {
			src: {
				light: "/assets/brand/logo-white.svg",
				dark: "/assets/brand/logo-white.svg",
			},
			width: 80,
			alt: "VerifyAfrica",
			href: "/",
		},
	},
	metadata: {
		title: "VerifyAfrica Docs",
		description: "VerifyAfrica API Documentation",
	},
	navigation: endpointNavigation,
	redirects: [{ from: "/", to: "/introduction" }],
	apis: [
		{
			type: "file",
			input: "../config/routes.oas.json",
			path: "api",
		},
	],
	theme: {
		light: {
			primary: "#009688",
			primaryForeground: "#1B263B",
		},
		dark: {
			primary: "#009688",
			primaryForeground: "#1B263B",
		},
	},
};

export default config;
