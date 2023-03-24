import Fuse from "fuse.js";
import React from "react";
import { FormControl } from "react-bootstrap";
import InputGroup from "react-bootstrap/InputGroup";
import { ReactComponent as SearchIcon } from "src/images/search.svg";
import { ReactComponent as DeleteIcon } from "src/images/x.svg";
import { getAllExperiments_experiments } from "src/types/getAllExperiments";
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
  const [searchTerms, setSearchTerms] = React.useState("");
  const [clearIcon, setClearIcon] = React.useState(false);
  const handleClick = () => {
    setSearchTerms("");
    setClearIcon(false);
    onChange(experiments);
  };

  const [timer, setTimer] = React.useState<NodeJS.Timeout | null>(null);

  const handleChange = (event: {
    target: { value: React.SetStateAction<string> };
  }) => {
    let inputValue = event.target.value as string;
    // Check if the input value already has a space at the end
    if (
      inputValue.length > 0 &&
      inputValue.charAt(inputValue.length - 1) !== " "
    ) {
      // If not, add a space at the end
      inputValue = inputValue + " ";
    }

    setSearchTerms(event.target.value);
    if (timer) {
      clearTimeout(timer);
    }
    if (event.target.value) {
      setClearIcon(true);

      const newTimer = setTimeout(() => {
        const results = fuse.search(inputValue);

        const searchResults = results.map((character) => character.item);
        onChange(searchResults);
      }, 700);

      setTimer(newTimer);
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
        value={searchTerms}
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
            right: "4px",
            zIndex: 99999,
            backgroundColor: "white",
            borderLeft: "1px solid lightgrey",
            paddingLeft: "0.5em",
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
