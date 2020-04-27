import faker from "faker";
import { AutoIncrementField, Factory, Field } from "experimenter/tests/factory";
import {
  PLATFORM_WINDOWS,
  PLATFORM_WINDOWS_LABEL,
  PLATFORM_MAC,
  PLATFORM_MAC_LABEL,
} from "experimenter/components/constants";

export class VariantsFactory extends Factory {
  getFields() {
    return {
      id: new AutoIncrementField(),
      description: new Field(faker.lorem.sentence),
      name: new Field(faker.lorem.sentence),
      ratio: new Field(() =>
        faker.random.number({ min: 1, max: 100 }).toString(),
      ),
      is_control: false,
    };
  }
}

export class GenericDataFactory extends Factory {
  getFields() {
    return {
      design: new Field(faker.lorem.paragraph),
      variants: [],
      type: "addon",
    };
  }
  postGeneration() {
    const { generateVariants } = this.options;
    if (generateVariants) {
      const variants = [];
      for (let i = 0; i < generateVariants; i++) {
        variants.push(VariantsFactory.build());
      }
      this.data.variants = [...this.data.variants, ...variants];
    }
    if (this.data.variants.length) {
      this.data.variants[0].is_control = true;
    }
  }
}

export class AddonRolloutFactory extends Factory {
  getFields() {
    return {
      rollout_type: "addon",
      design: new Field(faker.lorem.paragraph),
      addon_release_url: new Field(faker.internet.url),
      pref_name: null,
      pref_type: null,
      pref_value: null,
    };
  }
}

export class PrefRolloutFactory extends Factory {
  getFields() {
    return {
      rollout_type: "pref",
      design: new Field(faker.lorem.paragraph),
      preferences: [
        {
          pref_name: "browser.enabled",
          pref_type: "bool",
          pref_value: "true",
        },
      ],
    };
  }
}

export class AddonDataFactory extends GenericDataFactory {
  getFields() {
    return {
      is_branched_addon: false,
      addon_release_url: new Field(faker.internet.url),
      variants: [],
      type: "addon",
    };
  }
}

export class PrefVariantsFactory extends VariantsFactory {
  getFields() {
    return {
      value: new Field(faker.lorem.sentence),
      ...super.getFields(),
    };
  }
}

export class PrefDataFactory extends Factory {
  getFields() {
    return {
      pref_name: new Field(faker.lorem.sentence),
      pref_type: "string",
      pref_branch: "default",
      variants: [],
    };
  }

  postGeneration() {
    const { generateVariants } = this.options;
    if (generateVariants) {
      const variants = [];
      for (let i = 0; i < generateVariants; i++) {
        variants.push(PrefVariantsFactory.build());
      }
      this.data.variants = [...this.data.variants, ...variants];
    }
    if (this.data.variants.length) {
      this.data.variants[0].is_control = true;
    }
  }
}

export class BranchedAddonDataFactory extends Factory {
  getFields() {
    return {
      is_branched_addon: true,
      variants: [],
    };
  }

  postGeneration() {
    const { generateVariants } = this.options;
    if (generateVariants) {
      const variants = [];
      for (let i = 0; i < generateVariants; i++) {
        variants.push(BranchedAddonVariantFactory.build());
      }
      this.data.variants = [...this.data.variants, ...variants];
    }
    if (this.data.variants.length) {
      this.data.variants[0].is_control = true;
    }
  }
}

export class BranchedAddonVariantFactory extends Factory {
  getFields() {
    return {
      id: new AutoIncrementField(),
      description: new Field(faker.lorem.sentence),
      name: new Field(faker.lorem.sentence),
      ratio: new Field(faker.random.number, { min: 1, max: 100 }),
      is_control: false,
      addon_release_url: new Field(faker.internet.url),
    };
  }
}

export class MultiPrefVariantDataFactory extends Factory {
  getFields() {
    return {
      pref_name: new Field(faker.lorem.sentence),
      pref_type: "string",
      pref_branch: "default",
      pref_value: new Field(faker.lorem.sentence),
      id: new AutoIncrementField(),
    };
  }
}

export class MainMultiPrefVariantDataFactory extends Factory {
  getFields() {
    return {
      id: new AutoIncrementField(),
      description: new Field(faker.lorem.sentence),
      name: new Field(faker.lorem.sentence),
      ratio: new Field(faker.random.number, { min: 1, max: 100 }),
      is_control: false,
      preferences: [],
    };
  }

  postGeneration() {
    const preferences = [];
    for (let i = 0; i < 2; i++) {
      preferences.push(MultiPrefVariantDataFactory.build());
    }
    this.data.preferences = [...this.data.preferences, ...preferences];
  }
}

export class MultiPrefDataFactory extends Factory {
  getFields() {
    return {
      is_multi_pref: true,
      variants: [],
    };
  }

  postGeneration() {
    const { generateVariants } = this.options;

    if (generateVariants) {
      const variants = [];
      for (let i = 0; i < generateVariants; i++) {
        variants.push(MainMultiPrefVariantDataFactory.build());
      }
      this.data.variants = [...this.data.variants, ...variants];
    }
    if (this.data.variants.length) {
      this.data.variants[0].is_control = true;
    }
  }
}

export class MessageVariantsFactory extends VariantsFactory {
  getFields() {
    return {
      value: new Field(faker.lorem.paragraph),
      ...super.getFields(),
    };
  }
}

export class MessageDataFactory extends Factory {
  getFields() {
    return {
      variants: [],
    };
  }

  postGeneration() {
    const { generateVariants } = this.options;
    if (generateVariants) {
      const variants = [];
      for (let i = 0; i < generateVariants; i++) {
        variants.push(MessageVariantsFactory.build());
      }
      this.data.variants = [...this.data.variants, ...variants];
    }
    if (this.data.variants.length) {
      this.data.variants[0].is_control = true;
    }
  }
}

export class TimelinePopDataFactory extends Factory {
  getFields() {
    return {
      proposed_start_date: "2050-01-01",
      proposed_duration: 50,
      proposed_enrollment: 25,
      population_percent: 25.0,
      firefox_channel: "release",
      firefox_min_version: "67.0",
      firefox_max_version: "68.0",
      locales: [{ value: "NP", label: "Nepali" }],
      countries: [{ value: "US", label: "United States" }],
      platforms: [
        { value: PLATFORM_WINDOWS, label: PLATFORM_WINDOWS_LABEL },
        { value: PLATFORM_MAC, label: PLATFORM_MAC_LABEL },
      ],
      client_matching: "client matching data",
    };
  }
}
