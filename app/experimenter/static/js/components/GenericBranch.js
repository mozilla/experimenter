import React from "react";
import { Button, Row, Col, FormControl } from "react-bootstrap";
import DesignInput from "experimenter/components/DesignInput";
export default function GenericBranch(props) {
  return (
    <div key={props.id}>
      <Row className="mb-3">
        <Col md={{ span: 4, offset: 3 }}>
          {props.values.is_control ? (
            <h4>Control Branch</h4>
          ) : (
            <h4>Branch {props.id}</h4>
          )}
        </Col>
        <Col md={5} className="text-right">
          {props.id != 0 ? (
            <Button
              variant="danger"
              onClick={()=>props.remove(props.index)}
              id="remove-branch-button"
            >
              <span className="fas fa-times"></span> Remove Branch
            </Button>
          ) : null}
        </Col>
      </Row>
      <DesignInput
        label="Branch Size"
        name={"variants[" + props.id + "][ratio]"}
        id={"variants-" + props.id + "-ratio"}
        value={props.values.ratio}
        error={
          props.errors.variants ? props.errors.variants[props.index].ratio : ""
        }
        helpContent={
          <div>
            <p>
              Choose the size of this branch represented as a whole number. The
              size of all branches together must be equal to 100. It does not
              have to be exact, so these sizes are simply a recommendation of
              the relative distribution of the branches.
            </p>
            <p>
              <strong>Example:</strong> 50
            </p>
          </div>
        }
      />
      <DesignInput
        label="Name"
        name={"variants[" + props.id + "][name]"}
        id={"variants-" + props.id + "-name"}
        value={props.values.name}
        error={
          props.errors.variants ? props.errors.variants[props.index].name : ""
        }
        helpContent={
          <div>
            <p>
              The control group should represent the users receiving the
              existing, unchanged version of what you're testing. For example,
              if you're testing making a button larger to see if users click on
              it more often, the control group would receive the existing button
              size. You should name your control branch based on the experience
              or functionality that group of users will be receiving. Don't name
              it 'Control Group', we already know it's the control group!
            </p>
            <p>
              <strong>Example:</strong> Normal Button Size
            </p>
          </div>
        }
      />
      <DesignInput
        label="Description"
        name={"variants[" + props.id + "][description]"}
        id={"variants-" + props.id + "-description"}
        as="textarea"
        rows="3"
        value={props.values.description}
        error={
          props.errors.variants
            ? props.errors.variants[props.index].description
            : ""
        }
        helpContent={
          <div>
            <p>
              Describe the experience or functionality the control group will
              receive in more detail.
            </p>
            <p>
              <strong>Example:</strong> The control group will receive the
              existing 80px sign in button located at the top right of the
              screen.
            </p>
          </div>
        }
      />
      <FormControl
        className="d-none"
        name={"variants[" + props.id + "][is_control]"}
        value={props.id == 0 ? true : false}
      />
      <FormControl
        className="d-none"
        name={"variants[" + props.id + "][id]"}
        value={props.values.id}
      />
      <hr className="heavy-line my-5" />
    </div>
  );
}
