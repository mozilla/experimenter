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

const branchesDiv = document.getElementById("react-branches-form");

function PrefForm(props) {
  return (
    <div>
      <Row>
        <Col md={{ span: 4, offset: 3 }}>
          <h4>Firefox Pref</h4>
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Pref Name</strong>
          </FormLabel>
          <br />
          <a href="/">help</a>
        </Col>
        <Col md={9}>
          <FormControl
            type="text"
            name="pref-name"
            value={props.pref_key}
            onChange={props.handleInputChange}
          />
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Pref Type</strong>
          </FormLabel>
          <br />
          <a href="/">help</a>
        </Col>
        <Col md={9}>
          <FormControl as="select"
            type="text"
            name="pref-type"
            value={props.pref_type}
            onChange={props.handleInputChange}
          >
            <option>Firefox Pref Type</option>
            <option>boolean</option>
            <option>integer</option>
            <option>string</option>
            <option>json string</option>
          </FormControl>
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Pref Branch</strong>
          </FormLabel>
          <br />
          <a href="/">help</a>
        </Col>
        <Col md={9}>
          <FormControl
            type="text"
            name="pref-branch"
            value={props.pref_branch}
            onChange={props.handleInputChange}
          />
        </Col>
      </Row>
    </div>
  );
}

function AddonForm(props) {
  return (
    <div>
      <Row>
        <Col md={{ span: 4, offset: 3 }}>
          <h4>Firefox Add-On</h4>
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Active Experiment Name</strong>
          </FormLabel>
          <br />
          <a href="/">help</a>
        </Col>
        <Col md={9}>
          <FormControl
            type="text"
            name="addon-experiment-id"
            onChange={props.handleInputChange}
            value={props.addon_experiment_id}
          />
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Signed Release URL</strong>
          </FormLabel>
          <br />
          <a href="/">help</a>
        </Col>
        <Col md={9}>
          <FormControl
            type="text"
            name="addon-release-url"
            onChange={props.handleInputChange}
            value={props.addon_release_url}
          />
        </Col>
      </Row>
    </div>
  );
}

function GenericForm(props) {
  return (
    <div>
      <Row>
        <Col md={{ span: 4, offset: 3 }}>
          <h4>Generic</h4>
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Design</strong>
          </FormLabel>
          <br />
          <a href="/">help</a>
        </Col>
        <Col md={9}>
          <FormControl
            as="textarea"
            name="design"
            rows={4}
            value={props.design}
            onChange={props.handleInputChange}
          />
        </Col>
      </Row>
    </div>
  );
}

function TypeForm(props) {
  const type = props.type;

  if (type == "pref") {
    return <PrefForm {...props}/>;
  } else if (type == "addon") {
    return <AddonForm {...props}/>;
  } else {
    return <GenericForm {...props}/>;
  }
}

function Error(props) {
  console.log(props.error);
  return (
    <div  className="invalid-feedback my-2">
      <span className="fas fa-exclamation"></span> {props.error}
    </div>
  )
}

export default class DesignForm extends React.Component {
  constructor(props) {
    super(props);

    this.slug = props.slug

    this.addBranch = this.addBranch.bind(this);
    this.removeBranch = this.removeBranch.bind(this);

    this.updateRatio = this.updateRatio.bind(this);
    this.updateName = this.updateName.bind(this);
    this.updateDescription = this.updateDescription.bind(this);
    this.updateValue = this.updateValue.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);

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
      errors: {}
    };
  }

  componentDidMount() {
    const that = this;

    let url;
    if (this.state.type == "pref") {
      url = `/api/v1/experiments/${this.slug}/design-pref`
    } else if (this.state.type == "addon") {
      url = `/api/v1/experiments/${this.slug}/design-addon`
    } else {
      url = `/api/v1/experiments/${this.slug}/design-generic`
    }

    fetch(url)
      .then(function(response) {
        return response.json();
      })
      .then(function(json) {

        if (json.variants == "") {
          return that.setState({
            type: json.type,
            pref_key: json.pref_key,
            pref_type: json.pref_type,
            pref_branch: json.pref_branch,
            addon_experiment_id: json.addon_experiment_id,
            addon_release_url:json.addon_release_url,
            design: json.design
          })
        } else {
          return that.setState({
            type: json.type,
            pref_key: json.pref_key,
            pref_type: json.pref_type,
            pref_branch: json.pref_branch,
            addon_experiment_id: json.addon_experiment_id,
            addon_release_url:json.addon_release_url,
            design: json.design,
            variants: json.variants
          });
        }
      });
  }

  addBranch(e) {
    e.preventDefault();
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

  removeBranch(e) {
    e.preventDefault();
    this.state.variants.splice(e.target.dataset.index, 1);

    this.setState({ variants: this.state.variants });
  }

  updateRatio(e) {
    this.state.variants[e.target.dataset.index].ratio = e.target.value
    this.setState({variants: this.state.variants})
  }

  updateName(e) {
    this.state.variants[e.target.dataset.index].name = e.target.value
    this.setState({variants: this.state.variants})

  }

  updateDescription(e) {
    var stateCopy = { ...this.state.variants };
    stateCopy[e.target.dataset.index].description = e.target.value;

    this.setState(stateCopy);
  }

  updateValue(e) {
    var stateCopy = { ...this.state.variants };
    stateCopy[e.target.dataset.index].value = e.target.value;

    this.setState(stateCopy);
  }

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

  async handleSubmit(e) {
    e.preventDefault();

    const data = new FormData(e.target);

    var object = {};
    data.forEach((value, key) => {object[key] = value});

    let url;

    if (this.state.type == "pref") {
      url = `/api/v1/experiments/${this.slug}/design-pref`
    } else if (this.state.type == "addon") {
      url = `/api/v1/experiments/${this.slug}/design-addon`
    } else {
      url = `/api/v1/experiments/${this.slug}/design-generic`
    }

    const res = await fetch(url, {
      method: "PUT",
      body: JSON.stringify(this.state),
      headers: {
        "Content-Type": "application/json"
      }
    });


    if (res.status == "200") {
      location.replace(`/experiments/${this.slug}`)
    }

    const json = await res.json();
    this.handleValidationErrors(json);
  }

  

  render() {
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
                        X Remove Branch
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
                    {this.state.errors.branch_ratio ? <Error error={this.state.errors}/>  : ""}
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
                <Row>
                  <Col md={3} className="text-right mb-3">
                    <FormLabel>
                      <strong>Pref Value</strong>
                    </FormLabel>
                    <br />
                    <a href="/">help</a>
                  </Col>
                  <Col md={9}>
                    <FormControl
                      data-index={index}
                      type="text"
                      name={"variants-" + index + "-value"}
                      onChange={this.updateValue}
                      value={branch.value}
                      className= {this.state.errors.branch_value ? "is-invalid" : "" }
                    />
                    {this.state.errors.branch_value ? <Error error={this.state.errors.branch_value}/>  : ""}
                  </Col>
                </Row>
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
                <a className="mr-1">X Cancel Editing</a>
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
