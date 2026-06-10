import type { ZudokuPlugin } from "zudoku";
import {
	SITE_KEYWORDS,
	SITE_NAME,
	SITE_TITLE,
	SITE_URL,
} from "./site-seo";
import { getPageOgImage, getPageSeo } from "./page-seo";

function buildKeywords(pageKeywords?: string[]): string {
	return [...new Set([...(pageKeywords ?? []), ...SITE_KEYWORDS])].join(", ");
}

export const seoPlugin: ZudokuPlugin = {
	getHead: ({ location }) => {
		const pathname = location.pathname;

		if (pathname.startsWith("/api")) {
			return undefined;
		}

		const page = getPageSeo(pathname);
		if (!page) {
			return undefined;
		}

		const ogTitle = `${page.title} | ${SITE_TITLE}`;
		const canonicalUrl = `${SITE_URL}${pathname === "/" ? "/introduction" : pathname.replace(/\/$/, "")}`;
		const ogImage = `${SITE_URL}${getPageOgImage(page)}`;
		const keywords = buildKeywords(page.keywords);

		return (
			<>
				<meta name="keywords" content={keywords} />
				<meta name="robots" content="index, follow" />
				<meta name="author" content={SITE_NAME} />
				<meta property="og:type" content="website" />
				<meta property="og:site_name" content={SITE_NAME} />
				<meta property="og:url" content={canonicalUrl} />
				<meta property="og:title" content={ogTitle} />
				<meta property="og:description" content={page.description} />
				<meta property="og:image" content={ogImage} />
				<meta property="og:image:alt" content={SITE_NAME} />
				<meta name="twitter:card" content="summary_large_image" />
				<meta name="twitter:title" content={ogTitle} />
				<meta name="twitter:description" content={page.description} />
				<meta name="twitter:image" content={ogImage} />
				<meta name="twitter:image:alt" content={SITE_NAME} />
			</>
		);
	},
};
