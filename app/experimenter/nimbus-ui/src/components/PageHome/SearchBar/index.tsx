import Fuse from "fuse.js";
import React from "react";
import { FormControl } from "react-bootstrap";
import InputGroup from "react-bootstrap/InputGroup";
import { ReactComponent as SearchIcon } from "../../../images/search.svg";
import { ReactComponent as DeleteIcon } from "../../../images/x.svg";
import { getAllExperiments_experiments } from "../../../types/getAllExperiments";
interface SearchBarProps {
  experiments: getAllExperiments_experiments[];
  onChange: any;
}
const searchKeys = [
  "application",
  "channel",
  "computedEndDate",
  "featureConfigs.description",
  "featureConfigs.name",
  "featureConfigs.schema",
  "featureConfigs.slug",
  "firefoxMaxVersion",
  "firefoxMinVersion",
  "hypothesis",
  "monitoringDashboardUrl",
  "name",
  "owner.username",
  "populationPercent",
  "projects.name",
  "publishStatus",
  "slug",
  "startDate",
  "status",
  "targetingConfig.description",
  "targetingConfig.label",
  "targetingConfig.value",
];

const SearchBar: React.FunctionComponent<SearchBarProps> = ({
  experiments,
  onChange,
}) => {
  const options = {
    includeScore: false,
    minMatchCharLength: 3,
    keys: searchKeys,
  };
  const myIndex = Fuse.createIndex(options.keys, experiments);
  const fuse = new Fuse(experiments, options, myIndex);
  const [value, setValue] = React.useState("");
  const [clearIcon, setClearIcon] = React.useState(false);
  const handleClick = () => {
    setValue("");
    setClearIcon(false);
    onChange(experiments);
  };
  const handleChange = (event: {
    target: { value: React.SetStateAction<string> };
  }) => {
    setValue(event.target.value);
    if (event.target.value) {
      setClearIcon(true);
      const result = fuse.search(value);

      const searchResults = result.map((character) => character.item);
      onChange(searchResults);
    } else {
      setClearIcon(false);
      onChange(experiments);
    }
  };

  return (
    <InputGroup className="mb-2">
      <InputGroup.Prepend>
        <InputGroup.Text>
          <SearchIcon
            width="15"
            height="15"
            role="img"
            aria-label="search icon"
          />
        </InputGroup.Text>
      </InputGroup.Prepend>
      <FormControl
        aria-label="Default"
        aria-describedby="inputGroup-sizing-default"
        onChange={handleChange}
        value={value}
        type="text"
        data-testid="SearchExperiments"
        placeholder="Search"
        style={{
          borderTopRightRadius: "4px",
          borderBottomRightRadius: "4px",
        }}
      />
      {clearIcon && (
        <DeleteIcon
          style={{
            position: "absolute",
            right: "0px",
            zIndex: 99999,
          }}
          data-testid="ClearSearchExperiments"
          onClick={handleClick}
          className="m-2"
        />
      )}
    </InputGroup>
  );
};

export default SearchBar;
