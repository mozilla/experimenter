import faker from "faker";
import { AutoIncrementField, Factory, Field } from "experimenter/tests/factory";

export class VariantsFactory extends Factory {
  getFields() {
    return {
      id: new AutoIncrementField(),
      description: new Field(faker.lorem.sentence),
      name: new Field(faker.lorem.word),
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
      designs: new Field(faker.lorem.paragraph),
      variants: [],
    };
  }
  postGeneration() {
    super.postGeneration();
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
      pref_key: null,
      pref_type: null,
      pref_value: null,
    };
  }
}

export class AddonDataFactory extends GenericDataFactory {
  getFields() {
    return {
      addon_release_url: new Field(faker.internet.url),
      variants: [],
      type: "addon",
    };
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
      name: new Field(faker.lorem.word),
      ratio: new Field(faker.random.number, { min: 1, max: 100 }),
      is_control: false,
      addon_release_url: new Field(faker.internet.url),
    };
  }
}
