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
  const resetWindowLocation = () => {
    /**
     * Specifically resets the address back to the default homepage
     */
    const url = new URL(`${window.location}`);
    url.searchParams.delete("search");
    window.history.pushState({}, "", `${url.origin + url.pathname}`);
  };
  const handleClick = () => {
    setSearchTerms("");
    setClearIcon(false);
    onChange(experiments);

    // clear stored search value
    localStorage.removeItem("nimbus-ui-search");

    // change address bar back to homepage
    resetWindowLocation();
  };
  const formRef = React.useRef<any>();

  const [timer, setTimer] = React.useState<NodeJS.Timeout | null>(null);

  React.useEffect(() => {
    const newtimer = setTimeout(() => {
      // get search term from url history
      const termFromURL = new URL(window.location as any).searchParams.get(
        "search",
      ) as string;

      if ("nimbus-ui-search" in localStorage) {
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
          window.HTMLInputElement.prototype,
          "value",
        )?.set;
        nativeInputValueSetter?.call(formRef.current, termFromURL);

        const event = new Event("input", { bubbles: true });
        formRef.current?.dispatchEvent(event);
      } else {
        resetWindowLocation();
      }
    }, 700);
    return () => clearTimeout(newtimer);
  }, []);

  const handleChange = (event: {
    target: { value: React.SetStateAction<string> };
  }) => {
    // add the search query to history state
    const url = new URL(`${window.location}`);
    url.searchParams.set("search", event.target.value as string);
    window.history.pushState({}, "", `${url}`);

    // Store url address to be used to go back
    localStorage.setItem("nimbus-ui-search", url.search);

    setSearchTerms(event.target.value);
    if (timer) {
      clearTimeout(timer);
    }
    if (event.target.value) {
      setClearIcon(true);

      const newTimer = setTimeout(() => {
        const results = fuse.search(event.target.value as string);

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
        ref={formRef}
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
