/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum NimbusExperimentApplicationEnum {
  DEMO_APP = "DEMO_APP",
  DESKTOP = "DESKTOP",
  FENIX = "FENIX",
  FOCUS_ANDROID = "FOCUS_ANDROID",
  FOCUS_IOS = "FOCUS_IOS",
  FXA = "FXA",
  IOS = "IOS",
  KLAR_ANDROID = "KLAR_ANDROID",
  KLAR_IOS = "KLAR_IOS",
  MONITOR = "MONITOR",
  VPN = "VPN",
}

export enum NimbusExperimentChannelEnum {
  AURORA = "AURORA",
  BETA = "BETA",
  DEVELOPER = "DEVELOPER",
  ESR = "ESR",
  NIGHTLY = "NIGHTLY",
  NO_CHANNEL = "NO_CHANNEL",
  PRODUCTION = "PRODUCTION",
  RELEASE = "RELEASE",
  STAGING = "STAGING",
  TESTFLIGHT = "TESTFLIGHT",
  UNBRANDED = "UNBRANDED",
}

export enum NimbusExperimentConclusionRecommendationEnum {
  CHANGE_COURSE = "CHANGE_COURSE",
  FOLLOWUP = "FOLLOWUP",
  GRADUATE = "GRADUATE",
  NONE = "NONE",
  RERUN = "RERUN",
  STOP = "STOP",
}

export enum NimbusExperimentDocumentationLinkEnum {
  DESIGN_DOC = "DESIGN_DOC",
  DS_JIRA = "DS_JIRA",
  ENG_TICKET = "ENG_TICKET",
  QA_TICKET = "QA_TICKET",
}

export enum NimbusExperimentFirefoxVersionEnum {
  FIREFOX_100 = "FIREFOX_100",
  FIREFOX_101 = "FIREFOX_101",
  FIREFOX_102 = "FIREFOX_102",
  FIREFOX_103 = "FIREFOX_103",
  FIREFOX_10301 = "FIREFOX_10301",
  FIREFOX_104 = "FIREFOX_104",
  FIREFOX_105 = "FIREFOX_105",
  FIREFOX_10501 = "FIREFOX_10501",
  FIREFOX_10502 = "FIREFOX_10502",
  FIREFOX_10503 = "FIREFOX_10503",
  FIREFOX_106 = "FIREFOX_106",
  FIREFOX_10601 = "FIREFOX_10601",
  FIREFOX_10602 = "FIREFOX_10602",
  FIREFOX_107 = "FIREFOX_107",
  FIREFOX_108 = "FIREFOX_108",
  FIREFOX_109 = "FIREFOX_109",
  FIREFOX_11 = "FIREFOX_11",
  FIREFOX_110 = "FIREFOX_110",
  FIREFOX_111 = "FIREFOX_111",
  FIREFOX_111_0_1 = "FIREFOX_111_0_1",
  FIREFOX_112 = "FIREFOX_112",
  FIREFOX_113 = "FIREFOX_113",
  FIREFOX_113_0_1 = "FIREFOX_113_0_1",
  FIREFOX_114 = "FIREFOX_114",
  FIREFOX_114_3_0 = "FIREFOX_114_3_0",
  FIREFOX_115 = "FIREFOX_115",
  FIREFOX_115_0_2 = "FIREFOX_115_0_2",
  FIREFOX_115_25 = "FIREFOX_115_25",
  FIREFOX_115_7 = "FIREFOX_115_7",
  FIREFOX_116 = "FIREFOX_116",
  FIREFOX_116_0_1 = "FIREFOX_116_0_1",
  FIREFOX_116_2_0 = "FIREFOX_116_2_0",
  FIREFOX_116_3_0 = "FIREFOX_116_3_0",
  FIREFOX_117 = "FIREFOX_117",
  FIREFOX_118 = "FIREFOX_118",
  FIREFOX_118_0_1 = "FIREFOX_118_0_1",
  FIREFOX_118_0_2 = "FIREFOX_118_0_2",
  FIREFOX_119 = "FIREFOX_119",
  FIREFOX_12 = "FIREFOX_12",
  FIREFOX_120 = "FIREFOX_120",
  FIREFOX_121 = "FIREFOX_121",
  FIREFOX_121_0_1 = "FIREFOX_121_0_1",
  FIREFOX_122 = "FIREFOX_122",
  FIREFOX_122_1_0 = "FIREFOX_122_1_0",
  FIREFOX_122_2_0 = "FIREFOX_122_2_0",
  FIREFOX_123 = "FIREFOX_123",
  FIREFOX_123_0_1 = "FIREFOX_123_0_1",
  FIREFOX_124 = "FIREFOX_124",
  FIREFOX_124_2_0 = "FIREFOX_124_2_0",
  FIREFOX_124_3_0 = "FIREFOX_124_3_0",
  FIREFOX_125 = "FIREFOX_125",
  FIREFOX_125_0_1 = "FIREFOX_125_0_1",
  FIREFOX_125_0_2 = "FIREFOX_125_0_2",
  FIREFOX_125_1_0 = "FIREFOX_125_1_0",
  FIREFOX_125_2_0 = "FIREFOX_125_2_0",
  FIREFOX_126 = "FIREFOX_126",
  FIREFOX_126_1_0 = "FIREFOX_126_1_0",
  FIREFOX_126_2_0 = "FIREFOX_126_2_0",
  FIREFOX_127 = "FIREFOX_127",
  FIREFOX_127_0_1 = "FIREFOX_127_0_1",
  FIREFOX_127_0_2 = "FIREFOX_127_0_2",
  FIREFOX_128 = "FIREFOX_128",
  FIREFOX_128_12 = "FIREFOX_128_12",
  FIREFOX_129 = "FIREFOX_129",
  FIREFOX_13 = "FIREFOX_13",
  FIREFOX_130 = "FIREFOX_130",
  FIREFOX_130_0_1 = "FIREFOX_130_0_1",
  FIREFOX_131 = "FIREFOX_131",
  FIREFOX_131_0_3 = "FIREFOX_131_0_3",
  FIREFOX_131_1_0 = "FIREFOX_131_1_0",
  FIREFOX_131_2_0 = "FIREFOX_131_2_0",
  FIREFOX_131_B4 = "FIREFOX_131_B4",
  FIREFOX_132 = "FIREFOX_132",
  FIREFOX_132_B6 = "FIREFOX_132_B6",
  FIREFOX_133 = "FIREFOX_133",
  FIREFOX_133_0_1 = "FIREFOX_133_0_1",
  FIREFOX_133_B8 = "FIREFOX_133_B8",
  FIREFOX_134 = "FIREFOX_134",
  FIREFOX_134_1_0 = "FIREFOX_134_1_0",
  FIREFOX_135 = "FIREFOX_135",
  FIREFOX_135_0_1 = "FIREFOX_135_0_1",
  FIREFOX_135_1_0 = "FIREFOX_135_1_0",
  FIREFOX_136 = "FIREFOX_136",
  FIREFOX_136_0_2 = "FIREFOX_136_0_2",
  FIREFOX_137 = "FIREFOX_137",
  FIREFOX_137_1_0 = "FIREFOX_137_1_0",
  FIREFOX_137_2_0 = "FIREFOX_137_2_0",
  FIREFOX_138 = "FIREFOX_138",
  FIREFOX_138_0_3 = "FIREFOX_138_0_3",
  FIREFOX_138_1_0 = "FIREFOX_138_1_0",
  FIREFOX_138_2_0 = "FIREFOX_138_2_0",
  FIREFOX_138_B3 = "FIREFOX_138_B3",
  FIREFOX_139 = "FIREFOX_139",
  FIREFOX_139_0_4 = "FIREFOX_139_0_4",
  FIREFOX_139_1_0 = "FIREFOX_139_1_0",
  FIREFOX_139_2_0 = "FIREFOX_139_2_0",
  FIREFOX_14 = "FIREFOX_14",
  FIREFOX_140 = "FIREFOX_140",
  FIREFOX_140_0_1 = "FIREFOX_140_0_1",
  FIREFOX_140_0_2 = "FIREFOX_140_0_2",
  FIREFOX_140_0_3 = "FIREFOX_140_0_3",
  FIREFOX_140_0_4 = "FIREFOX_140_0_4",
  FIREFOX_140_1_0 = "FIREFOX_140_1_0",
  FIREFOX_140_2_0 = "FIREFOX_140_2_0",
  FIREFOX_140_3_0 = "FIREFOX_140_3_0",
  FIREFOX_140_4_0 = "FIREFOX_140_4_0",
  FIREFOX_141 = "FIREFOX_141",
  FIREFOX_141_0_1 = "FIREFOX_141_0_1",
  FIREFOX_141_0_2 = "FIREFOX_141_0_2",
  FIREFOX_141_0_3 = "FIREFOX_141_0_3",
  FIREFOX_141_0_4 = "FIREFOX_141_0_4",
  FIREFOX_141_1_0 = "FIREFOX_141_1_0",
  FIREFOX_141_2_0 = "FIREFOX_141_2_0",
  FIREFOX_141_3_0 = "FIREFOX_141_3_0",
  FIREFOX_141_4_0 = "FIREFOX_141_4_0",
  FIREFOX_142 = "FIREFOX_142",
  FIREFOX_142_0_1 = "FIREFOX_142_0_1",
  FIREFOX_142_0_2 = "FIREFOX_142_0_2",
  FIREFOX_142_0_3 = "FIREFOX_142_0_3",
  FIREFOX_142_0_4 = "FIREFOX_142_0_4",
  FIREFOX_142_1_0 = "FIREFOX_142_1_0",
  FIREFOX_142_2_0 = "FIREFOX_142_2_0",
  FIREFOX_142_3_0 = "FIREFOX_142_3_0",
  FIREFOX_142_4_0 = "FIREFOX_142_4_0",
  FIREFOX_143 = "FIREFOX_143",
  FIREFOX_143_0_1 = "FIREFOX_143_0_1",
  FIREFOX_143_0_2 = "FIREFOX_143_0_2",
  FIREFOX_143_0_3 = "FIREFOX_143_0_3",
  FIREFOX_143_0_4 = "FIREFOX_143_0_4",
  FIREFOX_143_1_0 = "FIREFOX_143_1_0",
  FIREFOX_143_2_0 = "FIREFOX_143_2_0",
  FIREFOX_143_3_0 = "FIREFOX_143_3_0",
  FIREFOX_143_4_0 = "FIREFOX_143_4_0",
  FIREFOX_144 = "FIREFOX_144",
  FIREFOX_144_0_1 = "FIREFOX_144_0_1",
  FIREFOX_144_0_2 = "FIREFOX_144_0_2",
  FIREFOX_144_0_3 = "FIREFOX_144_0_3",
  FIREFOX_144_0_4 = "FIREFOX_144_0_4",
  FIREFOX_144_1_0 = "FIREFOX_144_1_0",
  FIREFOX_144_2_0 = "FIREFOX_144_2_0",
  FIREFOX_144_3_0 = "FIREFOX_144_3_0",
  FIREFOX_144_4_0 = "FIREFOX_144_4_0",
  FIREFOX_145 = "FIREFOX_145",
  FIREFOX_145_0_1 = "FIREFOX_145_0_1",
  FIREFOX_145_0_2 = "FIREFOX_145_0_2",
  FIREFOX_145_0_3 = "FIREFOX_145_0_3",
  FIREFOX_145_0_4 = "FIREFOX_145_0_4",
  FIREFOX_145_1_0 = "FIREFOX_145_1_0",
  FIREFOX_145_2_0 = "FIREFOX_145_2_0",
  FIREFOX_145_3_0 = "FIREFOX_145_3_0",
  FIREFOX_145_4_0 = "FIREFOX_145_4_0",
  FIREFOX_146 = "FIREFOX_146",
  FIREFOX_146_0_1 = "FIREFOX_146_0_1",
  FIREFOX_146_0_2 = "FIREFOX_146_0_2",
  FIREFOX_146_0_3 = "FIREFOX_146_0_3",
  FIREFOX_146_0_4 = "FIREFOX_146_0_4",
  FIREFOX_146_1_0 = "FIREFOX_146_1_0",
  FIREFOX_146_2_0 = "FIREFOX_146_2_0",
  FIREFOX_146_3_0 = "FIREFOX_146_3_0",
  FIREFOX_146_4_0 = "FIREFOX_146_4_0",
  FIREFOX_147 = "FIREFOX_147",
  FIREFOX_147_0_1 = "FIREFOX_147_0_1",
  FIREFOX_147_0_2 = "FIREFOX_147_0_2",
  FIREFOX_147_0_3 = "FIREFOX_147_0_3",
  FIREFOX_147_0_4 = "FIREFOX_147_0_4",
  FIREFOX_147_1_0 = "FIREFOX_147_1_0",
  FIREFOX_147_2_0 = "FIREFOX_147_2_0",
  FIREFOX_147_3_0 = "FIREFOX_147_3_0",
  FIREFOX_147_4_0 = "FIREFOX_147_4_0",
  FIREFOX_148 = "FIREFOX_148",
  FIREFOX_148_0_1 = "FIREFOX_148_0_1",
  FIREFOX_148_0_2 = "FIREFOX_148_0_2",
  FIREFOX_148_0_3 = "FIREFOX_148_0_3",
  FIREFOX_148_0_4 = "FIREFOX_148_0_4",
  FIREFOX_148_1_0 = "FIREFOX_148_1_0",
  FIREFOX_148_2_0 = "FIREFOX_148_2_0",
  FIREFOX_148_3_0 = "FIREFOX_148_3_0",
  FIREFOX_148_4_0 = "FIREFOX_148_4_0",
  FIREFOX_149 = "FIREFOX_149",
  FIREFOX_149_0_1 = "FIREFOX_149_0_1",
  FIREFOX_149_0_2 = "FIREFOX_149_0_2",
  FIREFOX_149_0_3 = "FIREFOX_149_0_3",
  FIREFOX_149_0_4 = "FIREFOX_149_0_4",
  FIREFOX_149_1_0 = "FIREFOX_149_1_0",
  FIREFOX_149_2_0 = "FIREFOX_149_2_0",
  FIREFOX_149_3_0 = "FIREFOX_149_3_0",
  FIREFOX_149_4_0 = "FIREFOX_149_4_0",
  FIREFOX_15 = "FIREFOX_15",
  FIREFOX_150 = "FIREFOX_150",
  FIREFOX_150_0_1 = "FIREFOX_150_0_1",
  FIREFOX_150_0_2 = "FIREFOX_150_0_2",
  FIREFOX_150_0_3 = "FIREFOX_150_0_3",
  FIREFOX_150_0_4 = "FIREFOX_150_0_4",
  FIREFOX_150_1_0 = "FIREFOX_150_1_0",
  FIREFOX_150_2_0 = "FIREFOX_150_2_0",
  FIREFOX_150_3_0 = "FIREFOX_150_3_0",
  FIREFOX_150_4_0 = "FIREFOX_150_4_0",
  FIREFOX_151 = "FIREFOX_151",
  FIREFOX_151_0_1 = "FIREFOX_151_0_1",
  FIREFOX_151_0_2 = "FIREFOX_151_0_2",
  FIREFOX_151_0_3 = "FIREFOX_151_0_3",
  FIREFOX_151_0_4 = "FIREFOX_151_0_4",
  FIREFOX_151_1_0 = "FIREFOX_151_1_0",
  FIREFOX_151_2_0 = "FIREFOX_151_2_0",
  FIREFOX_151_3_0 = "FIREFOX_151_3_0",
  FIREFOX_151_4_0 = "FIREFOX_151_4_0",
  FIREFOX_152 = "FIREFOX_152",
  FIREFOX_152_0_1 = "FIREFOX_152_0_1",
  FIREFOX_152_0_2 = "FIREFOX_152_0_2",
  FIREFOX_152_0_3 = "FIREFOX_152_0_3",
  FIREFOX_152_0_4 = "FIREFOX_152_0_4",
  FIREFOX_152_1_0 = "FIREFOX_152_1_0",
  FIREFOX_152_2_0 = "FIREFOX_152_2_0",
  FIREFOX_152_3_0 = "FIREFOX_152_3_0",
  FIREFOX_152_4_0 = "FIREFOX_152_4_0",
  FIREFOX_153 = "FIREFOX_153",
  FIREFOX_153_0_1 = "FIREFOX_153_0_1",
  FIREFOX_153_0_2 = "FIREFOX_153_0_2",
  FIREFOX_153_0_3 = "FIREFOX_153_0_3",
  FIREFOX_153_0_4 = "FIREFOX_153_0_4",
  FIREFOX_153_1_0 = "FIREFOX_153_1_0",
  FIREFOX_153_2_0 = "FIREFOX_153_2_0",
  FIREFOX_153_3_0 = "FIREFOX_153_3_0",
  FIREFOX_153_4_0 = "FIREFOX_153_4_0",
  FIREFOX_154 = "FIREFOX_154",
  FIREFOX_154_0_1 = "FIREFOX_154_0_1",
  FIREFOX_154_0_2 = "FIREFOX_154_0_2",
  FIREFOX_154_0_3 = "FIREFOX_154_0_3",
  FIREFOX_154_0_4 = "FIREFOX_154_0_4",
  FIREFOX_154_1_0 = "FIREFOX_154_1_0",
  FIREFOX_154_2_0 = "FIREFOX_154_2_0",
  FIREFOX_154_3_0 = "FIREFOX_154_3_0",
  FIREFOX_154_4_0 = "FIREFOX_154_4_0",
  FIREFOX_155 = "FIREFOX_155",
  FIREFOX_155_0_1 = "FIREFOX_155_0_1",
  FIREFOX_155_0_2 = "FIREFOX_155_0_2",
  FIREFOX_155_0_3 = "FIREFOX_155_0_3",
  FIREFOX_155_0_4 = "FIREFOX_155_0_4",
  FIREFOX_155_1_0 = "FIREFOX_155_1_0",
  FIREFOX_155_2_0 = "FIREFOX_155_2_0",
  FIREFOX_155_3_0 = "FIREFOX_155_3_0",
  FIREFOX_155_4_0 = "FIREFOX_155_4_0",
  FIREFOX_156 = "FIREFOX_156",
  FIREFOX_156_0_1 = "FIREFOX_156_0_1",
  FIREFOX_156_0_2 = "FIREFOX_156_0_2",
  FIREFOX_156_0_3 = "FIREFOX_156_0_3",
  FIREFOX_156_0_4 = "FIREFOX_156_0_4",
  FIREFOX_156_1_0 = "FIREFOX_156_1_0",
  FIREFOX_156_2_0 = "FIREFOX_156_2_0",
  FIREFOX_156_3_0 = "FIREFOX_156_3_0",
  FIREFOX_156_4_0 = "FIREFOX_156_4_0",
  FIREFOX_157 = "FIREFOX_157",
  FIREFOX_157_0_1 = "FIREFOX_157_0_1",
  FIREFOX_157_0_2 = "FIREFOX_157_0_2",
  FIREFOX_157_0_3 = "FIREFOX_157_0_3",
  FIREFOX_157_0_4 = "FIREFOX_157_0_4",
  FIREFOX_157_1_0 = "FIREFOX_157_1_0",
  FIREFOX_157_2_0 = "FIREFOX_157_2_0",
  FIREFOX_157_3_0 = "FIREFOX_157_3_0",
  FIREFOX_157_4_0 = "FIREFOX_157_4_0",
  FIREFOX_158 = "FIREFOX_158",
  FIREFOX_158_0_1 = "FIREFOX_158_0_1",
  FIREFOX_158_0_2 = "FIREFOX_158_0_2",
  FIREFOX_158_0_3 = "FIREFOX_158_0_3",
  FIREFOX_158_0_4 = "FIREFOX_158_0_4",
  FIREFOX_158_1_0 = "FIREFOX_158_1_0",
  FIREFOX_158_2_0 = "FIREFOX_158_2_0",
  FIREFOX_158_3_0 = "FIREFOX_158_3_0",
  FIREFOX_158_4_0 = "FIREFOX_158_4_0",
  FIREFOX_159 = "FIREFOX_159",
  FIREFOX_159_0_1 = "FIREFOX_159_0_1",
  FIREFOX_159_0_2 = "FIREFOX_159_0_2",
  FIREFOX_159_0_3 = "FIREFOX_159_0_3",
  FIREFOX_159_0_4 = "FIREFOX_159_0_4",
  FIREFOX_159_1_0 = "FIREFOX_159_1_0",
  FIREFOX_159_2_0 = "FIREFOX_159_2_0",
  FIREFOX_159_3_0 = "FIREFOX_159_3_0",
  FIREFOX_159_4_0 = "FIREFOX_159_4_0",
  FIREFOX_16 = "FIREFOX_16",
  FIREFOX_160 = "FIREFOX_160",
  FIREFOX_160_0_1 = "FIREFOX_160_0_1",
  FIREFOX_160_0_2 = "FIREFOX_160_0_2",
  FIREFOX_160_0_3 = "FIREFOX_160_0_3",
  FIREFOX_160_0_4 = "FIREFOX_160_0_4",
  FIREFOX_160_1_0 = "FIREFOX_160_1_0",
  FIREFOX_160_2_0 = "FIREFOX_160_2_0",
  FIREFOX_160_3_0 = "FIREFOX_160_3_0",
  FIREFOX_160_4_0 = "FIREFOX_160_4_0",
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
  FIREFOX_9601 = "FIREFOX_9601",
  FIREFOX_9602 = "FIREFOX_9602",
  FIREFOX_97 = "FIREFOX_97",
  FIREFOX_98 = "FIREFOX_98",
  FIREFOX_9830 = "FIREFOX_9830",
  FIREFOX_99 = "FIREFOX_99",
  FIREFOX_9910 = "FIREFOX_9910",
  NO_VERSION = "NO_VERSION",
}

export enum NimbusExperimentPublishStatusEnum {
  APPROVED = "APPROVED",
  IDLE = "IDLE",
  REVIEW = "REVIEW",
  WAITING = "WAITING",
}

export enum NimbusExperimentQAStatusEnum {
  GREEN = "GREEN",
  NOT_SET = "NOT_SET",
  RED = "RED",
  SELF_GREEN = "SELF_GREEN",
  SELF_RED = "SELF_RED",
  SELF_YELLOW = "SELF_YELLOW",
  YELLOW = "YELLOW",
}

export enum NimbusExperimentStatusEnum {
  COMPLETE = "COMPLETE",
  DRAFT = "DRAFT",
  LIVE = "LIVE",
  PREVIEW = "PREVIEW",
}

export interface BranchFeatureValueInput {
  featureConfig?: string | null;
  value?: string | null;
}

export interface BranchInput {
  id?: number | null;
  name: string;
  description: string;
  ratio: number;
  featureValues?: (BranchFeatureValueInput | null)[] | null;
  screenshots?: (BranchScreenshotInput | null)[] | null;
}

export interface BranchScreenshotInput {
  id?: number | null;
  image?: Upload | null;
  description?: string | null;
}

export interface DocumentationLinkInput {
  title: NimbusExperimentDocumentationLinkEnum;
  link: string;
}

export interface ExperimentCloneInput {
  parentSlug: string;
  name: string;
  rolloutBranchSlug?: string | null;
}

export interface ExperimentInput {
  application?: NimbusExperimentApplicationEnum | null;
  changelogMessage?: string | null;
  channel?: NimbusExperimentChannelEnum | null;
  conclusionRecommendations?: (NimbusExperimentConclusionRecommendationEnum | null)[] | null;
  countries?: (string | null)[] | null;
  documentationLinks?: (DocumentationLinkInput | null)[] | null;
  excludedExperimentsBranches?: NimbusExperimentBranchThroughExcludedInput[] | null;
  featureConfigIds?: (number | null)[] | null;
  firefoxMaxVersion?: NimbusExperimentFirefoxVersionEnum | null;
  firefoxMinVersion?: NimbusExperimentFirefoxVersionEnum | null;
  hypothesis?: string | null;
  id?: number | null;
  isArchived?: boolean | null;
  isEnrollmentPaused?: boolean | null;
  isFirstRun?: boolean | null;
  isLocalized?: boolean | null;
  isRollout?: boolean | null;
  isSticky?: boolean | null;
  languages?: (string | null)[] | null;
  legalSignoff?: boolean | null;
  locales?: (string | null)[] | null;
  localizations?: string | null;
  name?: string | null;
  populationPercent?: string | null;
  preventPrefConflicts?: boolean | null;
  primaryOutcomes?: (string | null)[] | null;
  projects?: (string | null)[] | null;
  proposedDuration?: string | null;
  proposedEnrollment?: string | null;
  proposedReleaseDate?: string | null;
  publicDescription?: string | null;
  publishStatus?: NimbusExperimentPublishStatusEnum | null;
  qaComment?: string | null;
  qaSignoff?: boolean | null;
  qaStatus?: NimbusExperimentQAStatusEnum | null;
  referenceBranch?: BranchInput | null;
  requiredExperimentsBranches?: NimbusExperimentBranchThroughRequiredInput[] | null;
  riskBrand?: boolean | null;
  riskMessage?: boolean | null;
  riskMitigationLink?: string | null;
  riskPartnerRelated?: boolean | null;
  riskRevenue?: boolean | null;
  secondaryOutcomes?: (string | null)[] | null;
  status?: NimbusExperimentStatusEnum | null;
  statusNext?: NimbusExperimentStatusEnum | null;
  subscribers?: NimbusExperimentSubscriberInput[] | null;
  takeawaysMetricGain?: boolean | null;
  takeawaysGainAmount?: string | null;
  takeawaysQbrLearning?: boolean | null;
  takeawaysSummary?: string | null;
  targetingConfigSlug?: string | null;
  totalEnrolledClients?: number | null;
  treatmentBranches?: (BranchInput | null)[] | null;
  useGroupId?: boolean | null;
  vpSignoff?: boolean | null;
  warnFeatureSchema?: boolean | null;
}

export interface NimbusExperimentBranchThroughExcludedInput {
  excludedExperiment: number;
  branchSlug?: string | null;
}

export interface NimbusExperimentBranchThroughRequiredInput {
  requiredExperiment: number;
  branchSlug?: string | null;
}

export interface NimbusExperimentSubscriberInput {
  email: string;
  subscribed: boolean;
}

//==============================================================
// END Enums and Input Objects
//==============================================================
