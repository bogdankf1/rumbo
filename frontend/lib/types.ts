export type SkillItem = {
  name: string;
  category: string;
  evidence: string;
  years: number | null;
  verified: boolean;
};

export type ResumeExtract = {
  full_name: string;
  headline: string;
  total_years_experience: number;
  seniority: string;
  skills: SkillItem[];
  roles: {
    title: string;
    company: string;
    start: string;
    end: string;
    summary: string;
    technologies: string[];
  }[];
  education: { degree: string; institution: string; year: string }[];
};

export type Resume = {
  id: string;
  name: string;
  source_filename: string | null;
  extracted: ResumeExtract;
  is_active: boolean;
  created_at: string;
};

export type ReqSkill = { name: string; evidence: string; verified: boolean };

export type JDExtract = {
  title: string;
  company: string;
  location: string | null;
  seniority: string | null;
  min_years_experience: number | null;
  required_skills: ReqSkill[];
  nice_to_have_skills: ReqSkill[];
  responsibilities: string[];
};

export type MatchEntry = {
  skill: string;
  jd_evidence: string;
  resume_evidence?: string;
};

export type MatchResult = {
  score: number;
  verdict: string;
  matched_required: MatchEntry[];
  missing_required: MatchEntry[];
  matched_nice: MatchEntry[];
  missing_nice: MatchEntry[];
  experience: {
    required_years: number | null;
    candidate_years: number;
    fit: number | null;
  };
};

export type Job = {
  id: string;
  seq: number;
  title: string;
  company: string;
  source: string;
  extracted: JDExtract;
  created_at: string;
  fit: MatchResult | null;
};

export type Citation = {
  id: string;
  doc_type: string;
  doc_id: string;
  doc_label: string;
  quote: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent: string | null;
  citations: Citation[] | null;
  created_at: string;
};

export function verdictColor(score: number): string {
  if (score >= 80) return "var(--color-strong)";
  if (score >= 60) return "var(--color-good)";
  if (score >= 40) return "var(--color-partial)";
  return "var(--color-weak)";
}
