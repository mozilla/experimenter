import React from "react";
import ReactDOM from "react-dom";
import {
  Button,
  Container,
  Row,
  Col,
  FormControl,
  FormLabel
} from "react-bootstrap";
import {boundMethod} from 'autobind-decorator';
import PrefValueInput from "pref-value-input";
import TypeForm from "type-form";
import Error from "error-form";
import HelpBox from "help-box";

const branchesDiv = document.getElementById("react-branches-form");


export default class DesignForm extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      type: props.expType,
      pref_key: "",
      pref_type: "",
      pref_branch: "",
      addon_experiment_id: "",
      addon_release_url: "",
      design: "",
      variants: [{
        ratio: null,
        name: "",
        description: "",
        value: "",
        is_control: true,
      }, {
        ratio: null,
        name: "",
        description: "",
        value: "",
        is_control: false,
      }],
      errors: {},
      loaded: false,
      help: {
        prefKey: false,
        prefType: false,
        prefBranch: false,
        addonExperimentId: false,
        addonReleaseUrl: false,
        design: false,
        variants: [{ratio: false, name: false, description: false, value: false}, {ratio: false, name: false, description: false, value: false}]
      }
    };
  }

  async componentDidMount () {
    const url = this.getApiUrl()

    const response = await fetch(url);

    const json = await response.json();

    if (json.variants.length == 0) {
      for (let i = 0; i < 2; i++) {
        let emptyBranch = {
          ratio: null,
          name: "",
          description: "",
          value: "",
          }
          if (i == 0) {
            emptyBranch.is_control = true;
          } else {
            emptyBranch.is_control = false;
          }
      json.variants.push(emptyBranch)
      }
    }
    json.loaded = true;
    return this.setState(json)
  }

@boundMethod
  addBranch(e) {
    let stateCopy = {...this.state}

    console.log(stateCopy.variants);
    stateCopy.variants.push({
      ratio: null,
      name: "",
      description: "",
      value: "",
      is_control: false,
    })
    stateCopy.help.variants.push({
      ratio: false,
      name: false,
      description: false,
      value: false
    })

    this.setState(stateCopy)
    // this.setState({
    //   variants: this.state.variants.concat({
    //     ratio: null,
    //     name: "",
    //     description: "",
    //     value: "",
    //     is_control: false,
    //   }),
    //   help: this.state.help.variants.concat({
        // ratio: false,
        // name: false,
        // description: false,
        // value: false
    //   })
    // });
  }

  @boundMethod
  removeBranch(e) {
    this.state.variants.splice(e.target.dataset.index, 1);
    this.setState({ variants: this.state.variants });
  }

  @boundMethod
  updateRatio(e) {
    this.state.variants[e.target.dataset.index].ratio = e.target.value
    this.setState({variants: this.state.variants})
  }

  @boundMethod
  updateName(e) {
    this.state.variants[e.target.dataset.index].name = e.target.value
    this.setState({variants: this.state.variants})

  }

  @boundMethod
  updateDescription(e) {
    var stateCopy = { ...this.state.variants };
    stateCopy[e.target.dataset.index].description = e.target.value;

    this.setState(stateCopy);
  }

  @boundMethod
  updateValue(e) {
    var stateCopy = { ...this.state.variants };
    stateCopy[e.target.dataset.index].value = e.target.value;

    this.setState(stateCopy);
  }

  @boundMethod
  handleInputChange(e) {
    if (e.target.name == "pref-name") {
      this.setState({pref_key: e.target.value})
    } else if (e.target.name == "pref-type") {
      this.setState({pref_type: e.target.value})
    } else if (e.target.name == "pref-branch") {
      this.setState({pref_branch: e.target.value})
    } else if (e.target.name == "design") {
      this.setState({design: e.target.value})
    } else if (e.target.name == "addon-experiment-id") {
      this.setState({addon_experiment_id: e.target.value})
    } else if (e.target.name == "addon-release-url") {
      this.setState({addon_release_url: e.target.value})
    }
  }

  handleValidationErrors(json) {
    this.setState({errors: json})
  }

  @boundMethod
  toggleHelp(e) {
    e.preventDefault();
    let stateCopy = {...this.state.help}
    if (e.target.id == "branch-ratio") {
      stateCopy.variants[e.target.dataset.index].ratio = !stateCopy.variants[e.target.dataset.index].ratio
      this.setState({help: stateCopy})
    } else if (e.target.id == "branch-name") {
      stateCopy.variants[e.target.dataset.index].name = !stateCopy.variants[e.target.dataset.index].name
      this.setState({help: stateCopy})
    } else if (e.target.id == "branch-description") {
      stateCopy.variants[e.target.dataset.index].description = !stateCopy.variants[e.target.dataset.index].description
      this.setState({help: stateCopy})
    } else if (e.target.id == "branch-value") {
      stateCopy.variants[e.target.dataset.index].value = !stateCopy.variants[e.target.dataset.index].value
      this.setState({help: stateCopy})
    } else if (e.target.id == "pref-key") {
      stateCopy.prefKey = !stateCopy.prefKey
      this.setState({help: stateCopy})
    } else if (e.target.id == "pref-type") {
      stateCopy.prefType = !stateCopy.prefType
      this.setState({help: stateCopy})
    } else if (e.target.id == "pref-branch") {
      stateCopy.prefBranch = !stateCopy.prefBranch
      this.setState({help: stateCopy})
    } else if (e.target.id == "design") {
      stateCopy.design = !stateCopy.design
      this.setState({help: stateCopy})
    } else if (e.target.id == "addon-experiment-id") {
      stateCopy.addonExperimentId = !stateCopy.addonExperimentId
      this.setState({help: stateCopy})
    } else if (e.target.id == "addon-release-url") {
      stateCopy.addonReleaseUrl = !stateCopy.addonReleaseUrl
      this.setState({help: stateCopy})
    }
  }

  getApiUrl() {
    return `/api/v1/experiments/${this.props.slug}/design-${this.state.type}/`;
  }

  @boundMethod
  async handleSubmit(e) {
    e.preventDefault();

    const data = new FormData(e.target);

    var object = {};
    data.forEach((value, key) => {object[key] = value});

    const url = this.getApiUrl()

    const res = await fetch(url, {
      method: "PUT",
      body: JSON.stringify(this.state),
      headers: {
        "Content-Type": "application/json"
      }
    });


    if (res.status == "200") {
      location.replace(`/experiments/${this.props.slug}/`)
    }

    const json = await res.json();
    this.handleValidationErrors(json);
  }

  render() {
    const dataExists = this.state.loaded;
    if (!dataExists) {
      return null;
    } else {
      return (
        <div>
          <Container>
            <form onSubmit={this.handleSubmit}>
              <TypeForm
                handleInputChange={this.handleInputChange}
                toggleHelp={this.toggleHelp}
                {...this.state}
              />
              <hr className="heavy-line my-5" />
              {this.state.variants.map((branch, index) => (
                <div key={index}>
                  <Row className="mb-3">
                    <Col md={{ span: 4, offset: 3 }}>
                      {index == 0 ? (
                        <h4>Control Branch</h4>
                      ) : (
                        <h4>Branch {index}</h4>
                      )}
                    </Col>
                    <Col md={5} className="text-right">
                      {index != 0 ? (
                        <Button
                          variant="danger"
                          data-index={index}
                          onClick={this.removeBranch}
                        >
                          <span className="fas fa-times"></span> Remove Branch
                        </Button>
                      ) : null}
                    </Col>
                  </Row>
                  <Row>
                    <Col md={3} className="text-right mb-3">
                      <FormLabel>
                        <strong>Branch Size</strong>
                      </FormLabel>
                      <br />
                      <a href="#" id="branch-ratio" data-index={index} onClick={this.toggleHelp}>help</a>
                    </Col>
                    <Col md={9}>
                      <FormControl
                        data-index={index}
                        type="text"
                        name={"variants-" + index + "-ratio"}
                        onChange={this.updateRatio}
                        value={branch.ratio}
                        className= {this.state.errors.branch_ratio ? "is-invalid" : "" }
                      />
                      {this.state.errors.branch_ratio ? <Error error={this.state.errors.branch_ratio}/>  : ""}
                      <HelpBox showing={this.state.help.variants[index].ratio}>
                        <p>
                          Choose the size of this branch represented as a
                          whole number. The size of all branches together
                          must be equal to 100. It does not have to be exact,
                          so these sizes are simply a recommendation of the
                          relative distribution of the branches.
                        </p>
                        <p>
                          <strong>Example:</strong> 50
                        </p>
                      </HelpBox>
                    </Col>
                  </Row>
                  <Row>
                    <Col md={3} className="text-right mb-3">
                      <FormLabel>
                        <strong>Name</strong>
                      </FormLabel>
                      <br />
                      <a href="#" id="branch-name" data-index={index} onClick={this.toggleHelp}>help</a>
                    </Col>
                    <Col md={9}>
                      <FormControl
                        data-index={index}
                        type="text"
                        name={"variants-" + index + "-name"}
                        onChange={this.updateName}
                        value={branch.name}
                        className= {this.state.errors.branch_name ? "is-invalid" : "" }
                      />
                      {this.state.errors.branch_name ? <Error error={this.state.errors.branch_name}/> : ""}
                      <HelpBox showing={this.state.help.variants[index].name}>
                        <p>
                          The control group should represent the users receiving the
                          existing, unchanged version of what you're testing. For
                          example, if you're testing making a button larger to see
                          if users click on it more often, the control group would
                          receive the existing button size. You should name your
                          control branch based on the experience or functionality
                          that group of users will be receiving. Don't name it
                          'Control Group', we already know it's the control group!
                        </p>
                        <p>
                          <strong>Example:</strong> Normal Button Size
                        </p>
                      </HelpBox>
                    </Col>
                  </Row>
                  <Row>
                    <Col md={3} className="text-right mb-3">
                      <FormLabel>
                        <strong>Description</strong>
                      </FormLabel>
                      <br />
                      <a href="#" id="branch-description" data-index={index} onClick={this.toggleHelp}>help</a>
                    </Col>
                    <Col md={9}>
                      <FormControl
                        as="textarea"
                        rows={3}
                        data-index={index}
                        type="text"
                        name={"variants-" + index + "-description"}
                        onChange={this.updateDescription}
                        value={branch.description}
                        className="mb-4"
                      />
                      <HelpBox showing={this.state.help.variants[index].description}>
                        <p>
                           Describe the experience or functionality the control
                           group will receive in more detail.
                        </p>
                        <p>
                          <strong>Example:</strong> The control group will
                          receive the existing 80px sign in button located
                          at the top right of the screen.
                        </p>
                      </HelpBox>
                    </Col>
                  </Row>
                  {this.state.type == "pref" ? < PrefValueInput updateValue={this.updateValue} index={index} toggleHelp={this.toggleHelp} {...this.state}/> : ""}
                  <hr className="heavy-line my-5" />
                </div>
              ))}
              <Row>
                <Col className="text-right">
                  <Button
                    variant="success"
                    className="mb-4"
                    onClick={this.addBranch}
                  >
                    + Add Branch
                  </Button>
                </Col>
              </Row>
              <Row>
                <Col className="text-right">
                  <a className="mr-1 btn btn-default" href={`/experiments/${this.props.slug}/`}><span className="fas fa-times"></span> Cancel Editing</a>
                  <Button variant="primary" type="submit" className="mr-1">
                    Save
                  </Button>
                  <Button variant="primary" type="submit">
                    Save and Continue
                  </Button>
                </Col>
              </Row>
            </form>
          </Container>
        </div>
      );
    }

  }
}
