import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUTPUT = join(__dirname, "../config/routes.oas.json");
const BASE_URL = "https://api.verifyafrica.io";

const categories = [
  {
    id: "identity-verification",
    name: "Identity Verification",
    endpoints: [
      {
        id: "id_document",
        name: "Document Verification",
        description:
          "Verify government-issued identity documents such as passports, national IDs, and driver's licenses across 47+ African countries.",
        linkMode: true,
        params: [
          { name: "email", type: "string", required: true, description: "Customer's email address. Used to send the hosted verification link." },
          { name: "country", type: "string", required: false, description: 'ISO 3166-1 alpha-2 country code (e.g., "NG", "ZA", "GH", "KE").' },
          { name: "language", type: "string", required: false, description: 'Language for the hosted verification page (e.g., "EN", "FR"). Defaults to "EN".' },
          { name: "ttl", type: "number", required: false, description: "Link expiry time in minutes. Allowed: 30, 60, 180, 360, 720, 1440, 2880. Defaults to 60." },
        ],
        sampleInput: { language: "EN", email: "customer@example.com", ttl: 60 },
      },
      {
        id: "face_match",
        name: "Facial Screening",
        description:
          "Perform real-time liveness detection and face match verification against a reference document.",
        linkMode: true,
        params: [
          { name: "email", type: "string", required: true, description: "Customer's email address. Used to send the hosted verification link." },
          { name: "country", type: "string", required: false, description: 'ISO 3166-1 alpha-2 country code (e.g., "NG", "ZA", "GH", "KE").' },
          { name: "language", type: "string", required: false, description: 'Language for the hosted verification page (e.g., "EN", "FR"). Defaults to "EN".' },
          { name: "ttl", type: "number", required: false, description: "Link expiry time in minutes. Allowed: 30, 60, 180, 360, 720, 1440, 2880. Defaults to 60." },
        ],
        sampleInput: { language: "EN", email: "customer@example.com", ttl: 60 },
      },
    ],
  },
  {
    id: "compliance-screening",
    name: "Compliance & Screening",
    endpoints: [
      {
        id: "aml_screening",
        name: "AML Screening",
        description: "Screen individuals against global sanctions lists, PEP databases, and adverse media sources.",
        params: [
          { name: "first_name", type: "string", required: true, description: "Subject's first name." },
          { name: "last_name", type: "string", required: true, description: "Subject's last name." },
          { name: "date_of_birth", type: "string", required: false, description: "Date of birth in YYYY-MM-DD format." },
          { name: "country", type: "string", required: false, description: "ISO 3166-1 alpha-2 country code." },
          { name: "nationality", type: "string", required: false, description: "Subject's nationality." },
        ],
        sampleInput: { first_name: "John", last_name: "Doe", date_of_birth: "1985-06-15", country: "NG" },
      },
      {
        id: "business_aml_screening",
        name: "Business AML Screening",
        description: "Screen businesses and corporate entities against global sanctions lists and adverse media.",
        params: [
          { name: "company_name", type: "string", required: true, description: "Legal name of the business entity." },
          { name: "country", type: "string", required: false, description: "Country of incorporation (ISO 3166-1 alpha-2)." },
          { name: "rc_number", type: "string", required: false, description: "Registration or company number." },
        ],
        sampleInput: { company_name: "Acme Corp Ltd", country: "NG", rc_number: "RC123456" },
      },
      {
        id: "kyb_screening",
        name: "KYB - Know Your Business",
        description: "Perform full Know Your Business checks including ownership structure, beneficial owners, and registry data.",
        params: [
          { name: "rc_number", type: "string", required: true, description: "Company registration number." },
          { name: "company_name", type: "string", required: false, description: "Legal name of the business (used for cross-validation)." },
        ],
        sampleInput: { rc_number: "RC789012", company_name: "TechStart Nigeria Ltd" },
      },
    ],
  },
  {
    id: "address-verification",
    name: "Address Verification",
    endpoints: [
      {
        id: "address_verification",
        name: "Address Verification",
        description: "Verify physical address records against government and utility databases across Africa.",
        params: [
          { name: "address", type: "string", required: true, description: "Full street address." },
          { name: "city", type: "string", required: true, description: "City or town name." },
          { name: "state", type: "string", required: false, description: "State or province." },
          { name: "country", type: "string", required: true, description: "ISO 3166-1 alpha-2 country code." },
        ],
        sampleInput: { address: "15 Adeola Odeku Street", city: "Lagos", state: "Lagos", country: "NG" },
      },
    ],
  },
  {
    id: "risk-crypto",
    name: "Risk & Crypto",
    endpoints: [
      {
        id: "risk_assessment",
        name: "Risk Assessment",
        description: "Assess the fraud and identity risk score for a given individual based on their identity data.",
        params: [
          { name: "id_number", type: "string", required: true, description: "The identity number to assess." },
          { name: "id_type", type: "string", required: true, description: 'Type of ID (e.g., "national_id", "passport", "bvn").' },
          { name: "country", type: "string", required: true, description: "ISO 3166-1 alpha-2 country code." },
        ],
        sampleInput: { id_number: "22222222222", id_type: "bvn", country: "NG" },
      },
      {
        id: "crypto_wallet_screening",
        name: "Crypto Wallet Screening",
        description: "Screen cryptocurrency wallet addresses for sanctions exposure, darknet activity, and illicit fund sources.",
        params: [
          { name: "wallet_address", type: "string", required: true, description: "The cryptocurrency wallet address to screen." },
          { name: "blockchain", type: "string", required: true, description: 'Blockchain network (e.g., "bitcoin", "ethereum", "tron").' },
        ],
        sampleInput: { wallet_address: "1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf", blockchain: "bitcoin" },
      },
    ],
  },
];

const governmentRegistry = {
  id: "government-registry",
  name: "Government Registry Checks",
  countries: [
    {
      id: "south-africa",
      flag: "🇿🇦",
      name: "South Africa",
      endpoints: [
        {
          id: "za_said_verification",
          name: "South Africa ID Verification",
          description: "Verify South African ID numbers against the Department of Home Affairs registry.",
          params: [
            { name: "id_number", type: "string", required: true, description: "13-digit South African ID number." },
            { name: "first_name", type: "string", required: false, description: "Subject's first name for cross-validation." },
            { name: "last_name", type: "string", required: false, description: "Subject's last name for cross-validation." },
          ],
          sampleInput: { id_number: "9001015001087", first_name: "John", last_name: "Doe" },
        },
      ],
    },
    {
      id: "nigeria",
      flag: "🇳🇬",
      name: "Nigeria",
      endpoints: [
        { id: "ng_bvn_verification", name: "Nigeria BVN Verification", description: "Verify Nigerian Bank Verification Numbers against the NIBSS database.", params: [{ name: "bvn", type: "string", required: true, description: "11-digit Bank Verification Number." }, { name: "first_name", type: "string", required: false, description: "First name for cross-validation." }, { name: "last_name", type: "string", required: false, description: "Last name for cross-validation." }, { name: "date_of_birth", type: "string", required: false, description: "Date of birth (YYYY-MM-DD)." }], sampleInput: { bvn: "22222222222", first_name: "John", last_name: "Doe" } },
        { id: "ng_nin_verification", name: "Nigeria NIN Verification", description: "Verify Nigerian National Identification Numbers against the NIMC database.", params: [{ name: "nin", type: "string", required: true, description: "11-digit National Identification Number." }, { name: "first_name", type: "string", required: false, description: "First name for cross-validation." }, { name: "last_name", type: "string", required: false, description: "Last name for cross-validation." }], sampleInput: { nin: "12345678901" } },
        { id: "ng_virtual_nin_verification", name: "Nigeria Virtual NIN", description: "Verify Nigerian Virtual National Identification Numbers issued by NIMC.", params: [{ name: "vnin", type: "string", required: true, description: "16-character Virtual NIN." }], sampleInput: { vnin: "AB123456789012CD" } },
        { id: "ng_advanced_phone_number_verification", name: "Nigeria Phone Verification", description: "Verify Nigerian phone numbers with advanced carrier and identity validation.", params: [{ name: "phone_number", type: "string", required: true, description: "Nigerian phone number (e.g., 08012345678)." }, { name: "first_name", type: "string", required: false, description: "First name for cross-validation." }, { name: "last_name", type: "string", required: false, description: "Last name for cross-validation." }], sampleInput: { phone_number: "08012345678" } },
        { id: "ng_phone_number_lookup", name: "Nigeria Phone Lookup", description: "Lookup subscriber information associated with a Nigerian phone number.", params: [{ name: "phone_number", type: "string", required: true, description: "Nigerian phone number to look up." }], sampleInput: { phone_number: "08012345678" } },
        { id: "ng_cac_lookup", name: "Nigeria CAC Lookup", description: "Lookup company records from the Nigerian Corporate Affairs Commission (CAC).", params: [{ name: "rc_number", type: "string", required: true, description: "CAC registration number (e.g., RC123456)." }, { name: "company_name", type: "string", required: false, description: "Company name for cross-validation." }], sampleInput: { rc_number: "RC123456" } },
        { id: "ng_passport_verification", name: "Nigeria Passport Verification", description: "Verify Nigerian international passport numbers against NIS records.", params: [{ name: "passport_number", type: "string", required: true, description: "Passport number (e.g., A12345678)." }, { name: "first_name", type: "string", required: false, description: "First name for cross-validation." }, { name: "last_name", type: "string", required: false, description: "Last name for cross-validation." }, { name: "date_of_birth", type: "string", required: false, description: "Date of birth (YYYY-MM-DD)." }], sampleInput: { passport_number: "A12345678" } },
      ],
    },
    {
      id: "ghana",
      flag: "🇬🇭",
      name: "Ghana",
      endpoints: [
        { id: "gh_passport_lookup", name: "Ghana Passport Lookup", description: "Lookup Ghanaian international passport records.", params: [{ name: "passport_number", type: "string", required: true, description: "Ghana passport number (e.g., G1234567)." }, { name: "first_name", type: "string", required: false, description: "First name for cross-validation." }], sampleInput: { passport_number: "G1234567" } },
        { id: "gh_voter_card_lookup", name: "Ghana Voter Card Lookup", description: "Lookup Ghanaian voter identification card records.", params: [{ name: "voter_id", type: "string", required: true, description: "Ghana voter ID number." }, { name: "first_name", type: "string", required: false, description: "First name for cross-validation." }], sampleInput: { voter_id: "1234567890" } },
        { id: "gh_ssnit_lookup", name: "Ghana SSNIT Lookup", description: "Lookup Ghana Social Security and National Insurance Trust (SSNIT) records.", params: [{ name: "ssnit_number", type: "string", required: true, description: "SSNIT number." }, { name: "first_name", type: "string", required: false, description: "First name for cross-validation." }], sampleInput: { ssnit_number: "C123456789012" } },
        { id: "gh_drivers_license_lookup", name: "Ghana Driver's License", description: "Lookup Ghanaian driver's license records from the DVLA registry.", params: [{ name: "license_number", type: "string", required: true, description: "Driver's license number." }, { name: "first_name", type: "string", required: false, description: "First name for cross-validation." }], sampleInput: { license_number: "DL123456789" } },
      ],
    },
    {
      id: "kenya",
      flag: "🇰🇪",
      name: "Kenya",
      endpoints: [
        { id: "ke_passport_lookup", name: "Kenya Passport Lookup", description: "Lookup Kenyan international passport records from immigration registries.", params: [{ name: "passport_number", type: "string", required: true, description: "Kenya passport number (e.g., A1234567)." }, { name: "first_name", type: "string", required: false, description: "First name for cross-validation." }], sampleInput: { passport_number: "A1234567" } },
        { id: "ke_national_id_lookup", name: "Kenya National ID Lookup", description: "Lookup Kenyan national ID records from the National Registration Bureau.", params: [{ name: "id_number", type: "string", required: true, description: "Kenya national ID number." }, { name: "first_name", type: "string", required: false, description: "First name for cross-validation." }], sampleInput: { id_number: "12345678" } },
        { id: "ke_phone_number_lookup", name: "Kenya Phone Lookup", description: "Lookup subscriber information associated with a Kenyan phone number.", params: [{ name: "phone_number", type: "string", required: true, description: "Kenyan phone number (e.g., 0712345678)." }], sampleInput: { phone_number: "0712345678" } },
        { id: "ke_tax_pin_verification", name: "Kenya Tax PIN Verification", description: "Verify Kenyan KRA Personal Identification Numbers.", params: [{ name: "tax_pin", type: "string", required: true, description: "Kenya Revenue Authority PIN (e.g., A123456789B)." }, { name: "name", type: "string", required: false, description: "Taxpayer name for cross-validation." }], sampleInput: { tax_pin: "A123456789B" } },
      ],
    },
  ],
};

const BULK_UNSUPPORTED = new Set(["id_document", "face_match"]);

function paramToSchema(param) {
  const schema = { type: param.type, description: param.description };
  if (param.type === "object" && param.nested) {
    schema.properties = Object.fromEntries(
      param.nested.map((n) => [n.name, paramToSchema(n)])
    );
    schema.type = "object";
  }
  return schema;
}

function buildInputDataSchema(params) {
  const properties = Object.fromEntries(
    params.map((p) => [p.name, paramToSchema(p)])
  );
  const required = params.filter((p) => p.required).map((p) => p.name);
  return { type: "object", properties, ...(required.length ? { required } : {}) };
}

function zuploRoute(forwardPath) {
  return {
    corsPolicy: "none",
    handler: {
      export: "urlForwardHandler",
      module: "$import(@zuplo/runtime)",
      options: { baseUrl: `${BASE_URL}${forwardPath}` },
    },
  };
}

function verificationResponse(verificationType) {
  return {
    "200": {
      description: "Verification completed successfully",
      content: {
        "application/json": {
          schema: { $ref: "#/components/schemas/VerificationResponse" },
          examples: {
            success: {
              summary: "Successful verification",
              value: {
                status: "success",
                data: {
                  id: "ver_9gjzgc36t",
                  verification_type: verificationType,
                  status: "verified",
                  created_at: "2026-02-09T08:01:42.891Z",
                  response_data: {
                    first_name: "John",
                    last_name: "Doe",
                    date_of_birth: "1990-01-15",
                    gender: "Male",
                  },
                },
              },
            },
          },
        },
      },
    },
    "400": { description: "Bad Request - Missing or invalid parameters" },
    "401": { description: "Unauthorized - Invalid or missing API key" },
    "403": { description: "Forbidden - Insufficient credits or inactive key" },
    "404": { description: "Not Found - Identity record not found" },
    "500": { description: "Internal Server Error" },
  };
}

function bulkResponse() {
  return {
    "200": {
      description: "Batch submitted and all results returned",
      content: {
        "application/json": {
          schema: { $ref: "#/components/schemas/BulkVerificationResponse" },
        },
      },
    },
    "207": { description: "Multi-Status - Batch submitted; some records failed" },
    "400": { description: "Bad Request - Missing or invalid batch parameters" },
    "401": { description: "Unauthorized - Invalid or missing API key" },
    "403": { description: "Forbidden - Insufficient credits for batch size" },
    "422": { description: "Unprocessable Entity - Batch size exceeds 100 records" },
    "500": { description: "Internal Server Error" },
  };
}

function singleOperation(endpoint, tag) {
  const inputSchema = buildInputDataSchema(endpoint.params);
  const requestProperties = {
    is_test: { type: "boolean", description: "Set to true for sandbox mode. Defaults to false.", default: false },
    verification_type: { type: "string", description: "The verification type identifier.", enum: [endpoint.id] },
    input_data: inputSchema,
  };
  if (endpoint.linkMode) {
    requestProperties.method_type = {
      type: "string",
      description: 'Verification mode: "onsite" for hosted link, "offsite" for direct verification.',
      enum: ["onsite", "offsite"],
    };
  }

  return {
    summary: endpoint.name,
    description: endpoint.description,
    operationId: `single-${endpoint.id}`,
    tags: [tag],
    security: [{ ApiKeyAuth: [] }],
    requestBody: {
      required: true,
      content: {
        "application/json": {
          schema: {
            type: "object",
            required: ["verification_type", "input_data"],
            properties: requestProperties,
          },
          examples: {
            default: {
              summary: "Sample request",
              value: {
                is_test: false,
                verification_type: endpoint.id,
                ...(endpoint.linkMode ? { method_type: "onsite" } : {}),
                input_data: endpoint.sampleInput,
              },
            },
          },
        },
      },
    },
    responses: verificationResponse(endpoint.id),
    "x-zuplo-route": zuploRoute("/api/verifications/requests/"),
  };
}

function bulkOperation(endpoint, tag) {
  const inputSchema = buildInputDataSchema(endpoint.params);
  const unsupported = BULK_UNSUPPORTED.has(endpoint.id);

  return {
    summary: endpoint.name,
    description: unsupported
      ? `${endpoint.description}\n\n**Note:** This verification type requires a hosted page and is **not supported** in bulk mode. Use the Single API instead.`
      : `${endpoint.description}\n\nSubmit this verification type as part of a bulk batch via \`POST /api/verifications/bulk/\`. Include up to **100** verification objects per request.`,
    operationId: `bulk-${endpoint.id}`,
    tags: [tag],
    security: [{ ApiKeyAuth: [] }],
    requestBody: {
      required: true,
      content: {
        "application/json": {
          schema: { $ref: "#/components/schemas/BulkVerificationRequest" },
          examples: {
            default: {
              summary: `Bulk batch with ${endpoint.name}`,
              value: {
                is_test: false,
                verifications: [
                  {
                    verification_type: endpoint.id,
                    input_data: endpoint.sampleInput,
                  },
                ],
              },
            },
          },
        },
      },
    },
    responses: bulkResponse(),
    "x-zuplo-route": zuploRoute("/api/verifications/bulk/"),
  };
}

const paths = {};
const tags = [];
const singleTagNames = [];
const bulkTagNames = [];

for (const category of categories) {
  const singleTag = `single-${category.id}`;
  const bulkTag = `bulk-${category.id}`;
  singleTagNames.push(singleTag);
  bulkTagNames.push(bulkTag);

  tags.push(
    { name: singleTag, description: `${category.name} — single verification requests.`, "x-displayName": category.name },
    { name: bulkTag, description: `${category.name} — bulk verification requests.`, "x-displayName": category.name }
  );

  for (const endpoint of category.endpoints) {
    const singlePath = `/api/verifications/requests/${endpoint.id}`;
    const bulkPath = `/api/verifications/bulk/${endpoint.id}`;
    paths[singlePath] = { post: singleOperation(endpoint, singleTag) };
    paths[bulkPath] = { post: bulkOperation(endpoint, bulkTag) };
  }
}

const govSingleTags = [];
const govBulkTags = [];

for (const country of governmentRegistry.countries) {
  const singleTag = `single-gov-${country.id}`;
  const bulkTag = `bulk-gov-${country.id}`;
  govSingleTags.push(singleTag);
  govBulkTags.push(bulkTag);

  const count = country.endpoints.length;
  const displayName = `${country.flag} ${country.name} (${count})`;
  tags.push(
    {
      name: singleTag,
      description: `Government registry checks for ${country.name}.`,
      "x-displayName": displayName,
    },
    {
      name: bulkTag,
      description: `Bulk government registry checks for ${country.name}.`,
      "x-displayName": displayName,
    }
  );

  for (const endpoint of country.endpoints) {
    const singlePath = `/api/verifications/requests/${endpoint.id}`;
    const bulkPath = `/api/verifications/bulk/${endpoint.id}`;
    paths[singlePath] = { post: singleOperation(endpoint, singleTag) };
    paths[bulkPath] = { post: bulkOperation(endpoint, bulkTag) };
  }
}

const spec = {
  openapi: "3.1.0",
  info: {
    version: "1.0.0",
    title: "Verify Africa API",
    description: `Identity verification, compliance screening, and government registry checks across Africa.

## Authentication

All endpoints require an API key passed in the \`X-API-KEY\` header.

## API Sections

- **Single** — Submit one verification at a time via \`POST /api/verifications/requests/\`
- **Bulk** — Submit up to 100 verifications per batch via \`POST /api/verifications/bulk/\`

## Base URL

\`${BASE_URL}\``,
    contact: {
      name: "Verify Africa Support",
      url: "https://verifyafrica.io",
      email: "support@verifyafrica.io",
    },
  },
  servers: [{ url: BASE_URL, description: "Production" }],
  security: [{ ApiKeyAuth: [] }],
  tags,
  "x-tagGroups": [
    {
      name: "Single",
      tags: [...singleTagNames, ...govSingleTags],
    },
    {
      name: "Bulk",
      tags: [...bulkTagNames, ...govBulkTags],
    },
  ],
  paths,
  components: {
    securitySchemes: {
      ApiKeyAuth: {
        type: "apiKey",
        in: "header",
        name: "X-API-KEY",
        description: "Your Verify Africa API key.",
      },
    },
    schemas: {
      VerificationResponse: {
        type: "object",
        properties: {
          status: { type: "string", example: "success" },
          data: {
            type: "object",
            properties: {
              id: { type: "string", description: "Unique verification ID." },
              verification_type: { type: "string" },
              status: { type: "string", description: "verified, not_found, failed, or completed." },
              created_at: { type: "string", format: "date-time" },
              verification_url: { type: "string", description: "Hosted verification URL (link mode only)." },
              response_data: { type: "object", description: "Parsed identity or screening data." },
            },
          },
        },
      },
      BulkVerificationRequest: {
        type: "object",
        required: ["verifications"],
        properties: {
          is_test: { type: "boolean", default: false },
          verifications: {
            type: "array",
            maxItems: 100,
            items: {
              type: "object",
              required: ["verification_type", "input_data"],
              properties: {
                verification_type: { type: "string", description: "Verification type identifier." },
                input_data: { type: "object", description: "Verification-specific input fields." },
              },
            },
          },
        },
      },
      BulkVerificationResponse: {
        type: "object",
        properties: {
          status: { type: "string", example: "success" },
          data: {
            type: "object",
            properties: {
              batch_id: { type: "string" },
              total: { type: "number" },
              submitted: { type: "number" },
              failed: { type: "number" },
              results: {
                type: "array",
                items: {
                  type: "object",
                  properties: {
                    index: { type: "number" },
                    id: { type: "string" },
                    verification_type: { type: "string" },
                    status: { type: "string" },
                    response_data: { type: ["object", "null"] },
                    error: { type: "string" },
                  },
                },
              },
              created_at: { type: "string", format: "date-time" },
            },
          },
        },
      },
    },
  },
};

function needsQuotedString(value) {
  return (
    value.includes("\n") ||
    value.includes(":") ||
    value.includes("#") ||
    value.startsWith(" ") ||
    value.endsWith(" ") ||
    /^[\[\]{}&,*?|>!'%@`"]/.test(value) ||
    /^(true|false|null|yes|no|on|off)$/i.test(value)
  );
}

function toYaml(value, indent = 0) {
  const pad = "  ".repeat(indent);

  if (value === null || value === undefined) return "null";
  if (typeof value === "boolean" || typeof value === "number") return String(value);

  if (typeof value === "string") {
    if (value.includes("\n")) {
      return `|\n${value
        .split("\n")
        .map((line) => `${pad}  ${line}`)
        .join("\n")}`;
    }
    if (needsQuotedString(value)) return JSON.stringify(value);
    return value;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return "[]";
    return value
      .map((item) => {
        if (typeof item === "object" && item !== null && !Array.isArray(item)) {
          const entries = Object.entries(item);
          const [[k0, v0], ...restEntries] = entries;
          const firstRendered = toYaml(v0, indent + 2);
          let block = `${pad}- ${k0}: ${firstRendered.includes("\n") ? `\n${firstRendered}` : firstRendered}`;
          for (const [k, v] of restEntries) {
            const rendered = toYaml(v, indent + 2);
            block += rendered.includes("\n")
              ? `\n${pad}  ${k}:\n${rendered}`
              : `\n${pad}  ${k}: ${rendered}`;
          }
          return block;
        }
        return `${pad}- ${toYaml(item, indent + 1)}`;
      })
      .join("\n");
  }

  return Object.entries(value)
    .map(([key, val]) => {
      const rendered = toYaml(val, indent + 1);
      if (rendered.includes("\n") && !rendered.startsWith("|")) {
        return `${pad}${key}:\n${rendered}`;
      }
      return `${pad}${key}: ${rendered}`;
    })
    .join("\n");
}

const yamlOutput = join(__dirname, "../config/openapi.yaml");
writeFileSync(OUTPUT, JSON.stringify(spec, null, 2) + "\n");
writeFileSync(yamlOutput, toYaml(spec) + "\n");
console.log(
  `Generated ${OUTPUT} and ${yamlOutput} with ${Object.keys(paths).length} paths.`
);
