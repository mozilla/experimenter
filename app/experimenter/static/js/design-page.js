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
    this.setState({
      variants: this.state.variants.concat({
        ratio: null,
        name: "",
        description: "",
        value: "",
        is_control: false,
      })
    });
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

  getApiUrl() {
    return `/api/v1/experiments/${this.props.slug}/design-${this.state.type}/`;
  }


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
      return null; // or load indicator
    } else {
      return (
        <div>
          <Container>
            <form onSubmit={this.handleSubmit}>
              <TypeForm
                handleInputChange={this.handleInputChange}
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
                          <span class="fas fa-times"></span> Remove Branch
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
                      <a href="/">help</a>
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
                    </Col>
                  </Row>
                  <Row>
                    <Col md={3} className="text-right mb-3">
                      <FormLabel>
                        <strong>Name</strong>
                      </FormLabel>
                      <br />
                      <a href="/">help</a>
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
                    </Col>
                  </Row>
                  <Row>
                    <Col md={3} className="text-right mb-3">
                      <FormLabel>
                        <strong>Description</strong>
                      </FormLabel>
                      <br />
                      <a href="/">help</a>
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
                    </Col>
                  </Row>
                  {this.state.type == "pref" ? < PrefValueInput updateValue={this.updateValue} index={index} {...this.state}/> : ""}
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
                  <a className="mr-1 btn btn-default" href={`/experiments/${this.props.slug}/`}><span class="fas fa-times"></span> Cancel Editing</a>
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
