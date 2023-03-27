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

    // clear stored search value
    localStorage.removeItem("nimbus-ui-search");
  };

  const [timer, setTimer] = React.useState<NodeJS.Timeout | null>(null);

  React.useEffect(() => {
    const newtimer = setTimeout(() => {
      // get search term from localStorage
      let fetchedValues = localStorage.getItem("nimbus-ui-search");
      if (fetchedValues !== null) {
        fetchedValues = JSON.parse(fetchedValues);
        const searchValue = (fetchedValues as any)["searchValue"] as string;
        const results = (fetchedValues as any)["results"] as any[];
        const searchResults = results.map((character) => character.item);

        // Update components
        onChange(searchResults);
        setSearchTerms(searchValue);
        setClearIcon(true);
      }
    }, 700);
    return () => clearTimeout(newtimer);
  });

  const handleChange = (event: {
    target: { value: React.SetStateAction<string> };
  }) => {
    setSearchTerms(event.target.value);
    if (timer) {
      clearTimeout(timer);
    }
    if (event.target.value) {
      const searchValue = event.target.value as string;
      setClearIcon(true);

      const newTimer = setTimeout(() => {
        const results = fuse.search(searchTerms);
        const searchResults = results.map((character) => character.item);
        onChange(searchResults);

        // Store search query and results
        if (results.length > 0) {
          const nimbusResults = { searchValue, results };
          localStorage.setItem(
            "nimbus-ui-search",
            JSON.stringify(nimbusResults),
          );
        }
      }, 700);

      setTimer(newTimer);
    } else {
      setClearIcon(false);
      onChange(experiments);
      localStorage.removeItem("nimbus-ui-search");
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
