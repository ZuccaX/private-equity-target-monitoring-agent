export type CompanyStatus = "new" | "monitoring" | "contacted" | "priority";

export type Company = {
  id: number;
  name: string;
  website: string;
  sector: string;
  country: string;
  status: CompanyStatus;
  priorityScore: number;
  latestTrigger: string;
};

export const companies: Company[] = [
  {
    id: 1,
    name: "DataBridge AI",
    website: "https://databridge.ai",
    sector: "Data Infrastructure",
    country: "UK",
    status: "priority",
    priorityScore: 86,
    latestTrigger: "Expanded enterprise data platform into Germany",
  },
  {
    id: 2,
    name: "SecureFlow",
    website: "https://secureflow.io",
    sector: "Cybersecurity",
    country: "Netherlands",
    status: "monitoring",
    priorityScore: 74,
    latestTrigger: "Announced partnership with a European cloud provider",
  },
  {
    id: 3,
    name: "VerticalOps",
    website: "https://verticalops.com",
    sector: "Vertical SaaS",
    country: "Germany",
    status: "contacted",
    priorityScore: 69,
    latestTrigger: "New product launch for mid-market customers",
  },
  {
    id: 4,
    name: "FinCore Systems",
    website: "https://fincore.systems",
    sector: "FinTech Infrastructure",
    country: "UK",
    status: "new",
    priorityScore: 61,
    latestTrigger: "Recently hired a new VP of Sales",
  },
];