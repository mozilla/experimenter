/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum NimbusChangeLogOldStatus {
  COMPLETE = "COMPLETE",
  DRAFT = "DRAFT",
  LIVE = "LIVE",
  PREVIEW = "PREVIEW",
}

export enum NimbusChangeLogOldStatusNext {
  COMPLETE = "COMPLETE",
  DRAFT = "DRAFT",
  LIVE = "LIVE",
  PREVIEW = "PREVIEW",
}

export enum NimbusDocumentationLinkTitle {
  DESIGN_DOC = "DESIGN_DOC",
  DS_JIRA = "DS_JIRA",
  ENG_TICKET = "ENG_TICKET",
}

export enum NimbusExperimentApplication {
  DESKTOP = "DESKTOP",
  FENIX = "FENIX",
  FOCUS_ANDROID = "FOCUS_ANDROID",
  FOCUS_IOS = "FOCUS_IOS",
  IOS = "IOS",
  KLAR_ANDROID = "KLAR_ANDROID",
  KLAR_IOS = "KLAR_IOS",
}

export enum NimbusExperimentChannel {
  BETA = "BETA",
  NIGHTLY = "NIGHTLY",
  NO_CHANNEL = "NO_CHANNEL",
  RELEASE = "RELEASE",
  TESTFLIGHT = "TESTFLIGHT",
  UNBRANDED = "UNBRANDED",
}

export enum NimbusExperimentConclusionRecommendation {
  CHANGE_COURSE = "CHANGE_COURSE",
  FOLLOWUP = "FOLLOWUP",
  GRADUATE = "GRADUATE",
  RERUN = "RERUN",
  STOP = "STOP",
}

export enum NimbusExperimentDocumentationLink {
  DESIGN_DOC = "DESIGN_DOC",
  DS_JIRA = "DS_JIRA",
  ENG_TICKET = "ENG_TICKET",
}

export enum NimbusExperimentFirefoxMinVersion {
  FIREFOX_100 = "FIREFOX_100",
  FIREFOX_11 = "FIREFOX_11",
  FIREFOX_12 = "FIREFOX_12",
  FIREFOX_13 = "FIREFOX_13",
  FIREFOX_14 = "FIREFOX_14",
  FIREFOX_15 = "FIREFOX_15",
  FIREFOX_16 = "FIREFOX_16",
  FIREFOX_17 = "FIREFOX_17",
  FIREFOX_18 = "FIREFOX_18",
  FIREFOX_19 = "FIREFOX_19",
  FIREFOX_20 = "FIREFOX_20",
  FIREFOX_21 = "FIREFOX_21",
  FIREFOX_22 = "FIREFOX_22",
  FIREFOX_23 = "FIREFOX_23",
  FIREFOX_24 = "FIREFOX_24",
  FIREFOX_25 = "FIREFOX_25",
  FIREFOX_26 = "FIREFOX_26",
  FIREFOX_27 = "FIREFOX_27",
  FIREFOX_28 = "FIREFOX_28",
  FIREFOX_29 = "FIREFOX_29",
  FIREFOX_30 = "FIREFOX_30",
  FIREFOX_31 = "FIREFOX_31",
  FIREFOX_32 = "FIREFOX_32",
  FIREFOX_33 = "FIREFOX_33",
  FIREFOX_34 = "FIREFOX_34",
  FIREFOX_35 = "FIREFOX_35",
  FIREFOX_36 = "FIREFOX_36",
  FIREFOX_37 = "FIREFOX_37",
  FIREFOX_38 = "FIREFOX_38",
  FIREFOX_39 = "FIREFOX_39",
  FIREFOX_40 = "FIREFOX_40",
  FIREFOX_41 = "FIREFOX_41",
  FIREFOX_42 = "FIREFOX_42",
  FIREFOX_43 = "FIREFOX_43",
  FIREFOX_44 = "FIREFOX_44",
  FIREFOX_45 = "FIREFOX_45",
  FIREFOX_46 = "FIREFOX_46",
  FIREFOX_47 = "FIREFOX_47",
  FIREFOX_48 = "FIREFOX_48",
  FIREFOX_49 = "FIREFOX_49",
  FIREFOX_50 = "FIREFOX_50",
  FIREFOX_51 = "FIREFOX_51",
  FIREFOX_52 = "FIREFOX_52",
  FIREFOX_53 = "FIREFOX_53",
  FIREFOX_54 = "FIREFOX_54",
  FIREFOX_55 = "FIREFOX_55",
  FIREFOX_56 = "FIREFOX_56",
  FIREFOX_57 = "FIREFOX_57",
  FIREFOX_58 = "FIREFOX_58",
  FIREFOX_59 = "FIREFOX_59",
  FIREFOX_60 = "FIREFOX_60",
  FIREFOX_61 = "FIREFOX_61",
  FIREFOX_62 = "FIREFOX_62",
  FIREFOX_63 = "FIREFOX_63",
  FIREFOX_64 = "FIREFOX_64",
  FIREFOX_65 = "FIREFOX_65",
  FIREFOX_66 = "FIREFOX_66",
  FIREFOX_67 = "FIREFOX_67",
  FIREFOX_68 = "FIREFOX_68",
  FIREFOX_69 = "FIREFOX_69",
  FIREFOX_70 = "FIREFOX_70",
  FIREFOX_71 = "FIREFOX_71",
  FIREFOX_72 = "FIREFOX_72",
  FIREFOX_73 = "FIREFOX_73",
  FIREFOX_74 = "FIREFOX_74",
  FIREFOX_75 = "FIREFOX_75",
  FIREFOX_76 = "FIREFOX_76",
  FIREFOX_77 = "FIREFOX_77",
  FIREFOX_78 = "FIREFOX_78",
  FIREFOX_79 = "FIREFOX_79",
  FIREFOX_80 = "FIREFOX_80",
  FIREFOX_81 = "FIREFOX_81",
  FIREFOX_82 = "FIREFOX_82",
  FIREFOX_83 = "FIREFOX_83",
  FIREFOX_84 = "FIREFOX_84",
  FIREFOX_85 = "FIREFOX_85",
  FIREFOX_86 = "FIREFOX_86",
  FIREFOX_87 = "FIREFOX_87",
  FIREFOX_88 = "FIREFOX_88",
  FIREFOX_89 = "FIREFOX_89",
  FIREFOX_90 = "FIREFOX_90",
  FIREFOX_91 = "FIREFOX_91",
  FIREFOX_92 = "FIREFOX_92",
  FIREFOX_9201 = "FIREFOX_9201",
  FIREFOX_93 = "FIREFOX_93",
  FIREFOX_94 = "FIREFOX_94",
  FIREFOX_95 = "FIREFOX_95",
  FIREFOX_96 = "FIREFOX_96",
  FIREFOX_97 = "FIREFOX_97",
  FIREFOX_98 = "FIREFOX_98",
  FIREFOX_99 = "FIREFOX_99",
  NO_VERSION = "NO_VERSION",
}

export enum NimbusExperimentPublishStatus {
  APPROVED = "APPROVED",
  IDLE = "IDLE",
  REVIEW = "REVIEW",
  WAITING = "WAITING",
}

export enum NimbusExperimentStatus {
  COMPLETE = "COMPLETE",
  DRAFT = "DRAFT",
  LIVE = "LIVE",
  PREVIEW = "PREVIEW",
}

export interface BranchScreenshotType {
  image: Upload;
  description: string;
}

export interface DocumentationLinkType {
  title: NimbusExperimentDocumentationLink;
  link: string;
}

export interface ExperimentCloneInput {
  parentSlug: string;
  name: string;
  rolloutBranchSlug?: string | null;
}

export interface ExperimentInput {
  id?: number | null;
  isArchived?: boolean | null;
  status?: NimbusExperimentStatus | null;
  statusNext?: NimbusExperimentStatus | null;
  publishStatus?: NimbusExperimentPublishStatus | null;
  name?: string | null;
  hypothesis?: string | null;
  application?: NimbusExperimentApplication | null;
  publicDescription?: string | null;
  isEnrollmentPaused?: boolean | null;
  riskMitigationLink?: string | null;
  featureConfigId?: number | null;
  documentationLinks?: (DocumentationLinkType | null)[] | null;
  referenceBranch?: ReferenceBranchType | null;
  treatmentBranches?: (TreatmentBranchType | null)[] | null;
  primaryOutcomes?: (string | null)[] | null;
  secondaryOutcomes?: (string | null)[] | null;
  channel?: NimbusExperimentChannel | null;
  firefoxMinVersion?: NimbusExperimentFirefoxMinVersion | null;
  populationPercent?: string | null;
  proposedDuration?: number | null;
  proposedEnrollment?: string | null;
  targetingConfigSlug?: string | null;
  totalEnrolledClients?: number | null;
  changelogMessage?: string | null;
  riskPartnerRelated?: boolean | null;
  riskRevenue?: boolean | null;
  riskBrand?: boolean | null;
  countries?: (number | null)[] | null;
  locales?: (number | null)[] | null;
  conclusionRecommendation?: NimbusExperimentConclusionRecommendation | null;
  takeawaysSummary?: string | null;
}

export interface ReferenceBranchType {
  id?: number | null;
  name: string;
  description: string;
  ratio: number;
  featureEnabled?: boolean | null;
  featureValue?: string | null;
  screenshots?: (BranchScreenshotType | null)[] | null;
}

export interface TreatmentBranchType {
  id?: number | null;
  name: string;
  description: string;
  ratio: number;
  featureEnabled?: boolean | null;
  featureValue?: string | null;
  screenshots?: (BranchScreenshotType | null)[] | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================
