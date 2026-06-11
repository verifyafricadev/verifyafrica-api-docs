import { OG_IMAGE } from "./site-seo";

export type PageSeo = {
	title: string;
	description: string;
	keywords?: string[];
	image?: string;
};

export const PAGE_SEO: Record<string, PageSeo> = {
	"/introduction": {
		title:
			"VerifyAfrica: Identity Verification, Compliance Screening & Government Registry API",
		description:
			"Get started with the VerifyAfrica identity verification API. Verify documents, screen for AML risk, validate addresses, and query official registries across Nigeria, Ghana, Kenya, South Africa, and more.",
		keywords: [
			"VerifyAfrica API",
			"getting started",
			"identity verification API",
			"African KYC",
			"API authentication",
		],
	},
	"/endpoints/overview/identity-verification": {
		title: "Identity Verification",
		description:
			"Verify government-issued identity documents and perform biometric checks across 47+ African countries.",
		keywords: ["identity verification", "document verification", "face match", "biometrics"],
	},
	"/endpoints/id-document": {
		title: "Document Verification",
		description:
			"Verify government-issued identity documents such as passports, national IDs, and driver's licenses across 47+ African countries.",
		keywords: ["document verification", "passport verification", "national ID", "driver's license"],
	},
	"/endpoints/face-match": {
		title: "Facial Screening",
		description:
			"Perform real-time liveness detection and face match verification against a reference document.",
		keywords: ["face match", "liveness detection", "biometric verification", "facial screening"],
	},
	"/endpoints/overview/compliance-screening": {
		title: "Compliance & Screening",
		description:
			"Screen individuals and businesses against sanctions lists, PEP databases, adverse media, and corporate registries.",
		keywords: ["AML screening", "KYB", "compliance", "sanctions screening", "PEP"],
	},
	"/endpoints/aml-screening": {
		title: "AML Screening",
		description:
			"Screen individuals against global sanctions lists, PEP databases, and adverse media sources.",
		keywords: ["AML screening", "sanctions lists", "PEP database", "adverse media"],
	},
	"/endpoints/business-aml-screening": {
		title: "Business AML Screening",
		description:
			"Screen businesses and corporate entities against global sanctions lists and adverse media.",
		keywords: ["business AML", "corporate screening", "sanctions", "adverse media"],
	},
	"/endpoints/kyb-screening": {
		title: "KYB - Know Your Business",
		description:
			"Perform full Know Your Business checks including ownership structure, beneficial owners, and registry data.",
		keywords: ["KYB", "know your business", "beneficial owners", "corporate registry"],
	},
	"/endpoints/overview/address-verification": {
		title: "Address Verification",
		description:
			"Verify physical addresses against government and utility databases across Africa.",
		keywords: ["address verification", "physical address validation", "utility databases"],
	},
	"/endpoints/address-verification": {
		title: "Address Verification",
		description:
			"Verify physical address records against government and utility databases across Africa.",
		keywords: ["address verification", "address validation", "utility records"],
	},
	"/endpoints/overview/risk-crypto": {
		title: "Risk & Crypto",
		description:
			"Assess identity fraud risk and screen cryptocurrency wallets for illicit activity.",
		keywords: ["risk assessment", "crypto screening", "fraud risk", "wallet screening"],
	},
	"/endpoints/risk-assessment": {
		title: "Risk Assessment",
		description:
			"Assess the fraud and identity risk score for a given individual based on their identity data.",
		keywords: ["risk assessment", "fraud score", "identity risk"],
	},
	"/endpoints/crypto-wallet-screening": {
		title: "Crypto Wallet Screening",
		description:
			"Screen cryptocurrency wallet addresses for sanctions exposure, darknet activity, and illicit fund sources.",
		keywords: ["crypto wallet screening", "blockchain compliance", "sanctions exposure"],
	},
	"/endpoints/overview/government-registry": {
		title: "Government Registry Checks",
		description:
			"Verify identity and registry records against official government databases across South Africa, Nigeria, Ghana, and Kenya.",
		keywords: ["government registry", "official ID verification", "registry lookup"],
	},
	"/endpoints/overview/government-registry/south-africa": {
		title: "South Africa Government Registry",
		description: "Government registry verification endpoints for South Africa.",
		keywords: ["South Africa", "SA ID verification", "government registry"],
	},
	"/endpoints/za-said-verification": {
		title: "South Africa ID Verification",
		description:
			"Verify South African ID numbers against the Department of Home Affairs registry.",
		keywords: ["South Africa ID", "SA ID verification", "Home Affairs"],
	},
	"/endpoints/overview/government-registry/nigeria": {
		title: "Nigeria Government Registry",
		description: "Government registry verification endpoints for Nigeria.",
		keywords: ["Nigeria", "BVN", "NIN", "CAC", "government registry"],
	},
	"/endpoints/ng-bvn-verification": {
		title: "Nigeria BVN Verification",
		description: "Verify Nigerian Bank Verification Numbers against the NIBSS database.",
		keywords: ["BVN verification", "Nigeria BVN", "NIBSS", "bank verification number"],
	},
	"/endpoints/ng-nin-verification": {
		title: "Nigeria NIN Verification",
		description: "Verify Nigerian National Identification Numbers against the NIMC database.",
		keywords: ["NIN verification", "Nigeria NIN", "NIMC"],
	},
	"/endpoints/ng-virtual-nin-verification": {
		title: "Nigeria Virtual NIN",
		description: "Verify Nigerian Virtual National Identification Numbers issued by NIMC.",
		keywords: ["virtual NIN", "vNIN", "Nigeria", "NIMC"],
	},
	"/endpoints/ng-advanced-phone-number-verification": {
		title: "Nigeria Phone Verification",
		description:
			"Verify Nigerian phone numbers with advanced carrier and identity validation.",
		keywords: ["Nigeria phone verification", "phone number validation", "carrier lookup"],
	},
	"/endpoints/ng-phone-number-lookup": {
		title: "Nigeria Phone Lookup",
		description: "Lookup subscriber information associated with a Nigerian phone number.",
		keywords: ["Nigeria phone lookup", "subscriber information", "phone number lookup"],
	},
	"/endpoints/ng-cac-lookup": {
		title: "Nigeria CAC Lookup",
		description:
			"Lookup company records from the Nigerian Corporate Affairs Commission (CAC).",
		keywords: ["CAC lookup", "Nigeria company registry", "corporate affairs commission"],
	},
	"/endpoints/ng-passport-verification": {
		title: "Nigeria Passport Verification",
		description: "Verify Nigerian international passport numbers against NIS records.",
		keywords: ["Nigeria passport", "passport verification", "NIS"],
	},
	"/endpoints/overview/government-registry/ghana": {
		title: "Ghana Government Registry",
		description: "Government registry verification endpoints for Ghana.",
		keywords: ["Ghana", "government registry", "SSNIT", "voter card"],
	},
	"/endpoints/gh-passport-lookup": {
		title: "Ghana Passport Lookup",
		description: "Lookup Ghanaian international passport records.",
		keywords: ["Ghana passport", "passport lookup"],
	},
	"/endpoints/gh-voter-card-lookup": {
		title: "Ghana Voter Card Lookup",
		description: "Lookup Ghanaian voter identification card records.",
		keywords: ["Ghana voter card", "voter ID lookup"],
	},
	"/endpoints/gh-ssnit-lookup": {
		title: "Ghana SSNIT Lookup",
		description: "Lookup Ghana Social Security and National Insurance Trust (SSNIT) records.",
		keywords: ["SSNIT", "Ghana social security", "SSNIT lookup"],
	},
	"/endpoints/gh-drivers-license-lookup": {
		title: "Ghana Driver's License",
		description: "Lookup Ghanaian driver's license records from the DVLA registry.",
		keywords: ["Ghana driver's license", "DVLA", "license lookup"],
	},
	"/endpoints/overview/government-registry/kenya": {
		title: "Kenya Government Registry",
		description: "Government registry verification endpoints for Kenya.",
		keywords: ["Kenya", "government registry", "national ID", "KRA PIN"],
	},
	"/endpoints/ke-passport-lookup": {
		title: "Kenya Passport Lookup",
		description: "Lookup Kenyan international passport records from immigration registries.",
		keywords: ["Kenya passport", "passport lookup", "immigration registry"],
	},
	"/endpoints/ke-national-id-lookup": {
		title: "Kenya National ID Lookup",
		description: "Lookup Kenyan national ID records from the National Registration Bureau.",
		keywords: ["Kenya national ID", "national registration bureau"],
	},
	"/endpoints/ke-phone-number-lookup": {
		title: "Kenya Phone Lookup",
		description: "Lookup subscriber information associated with a Kenyan phone number.",
		keywords: ["Kenya phone lookup", "phone number lookup"],
	},
	"/endpoints/ke-tax-pin-verification": {
		title: "Kenya Tax PIN Verification",
		description: "Verify Kenyan KRA Personal Identification Numbers.",
		keywords: ["Kenya tax PIN", "KRA PIN", "tax identification"],
	},
};

export function getPageSeo(pathname: string): PageSeo | undefined {
	const normalized = pathname.replace(/\/$/, "") || "/introduction";
	const path = normalized === "/" ? "/introduction" : normalized;
	return PAGE_SEO[path];
}

export function getPageOgImage(page: PageSeo): string {
	return page.image ?? OG_IMAGE;
}
