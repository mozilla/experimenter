import React, { ChangeEvent } from "react";
import { Card, Table } from "react-bootstrap";
import Form from "react-bootstrap/Form";
import LinkExternal from "src/components/LinkExternal";
import { EXTERNAL_URLS } from "src/lib/constants";
import { getExperiment_experimentBySlug_signoffRecommendations } from "src/types/getExperiment";

type TableSignoffProps = {
  signoffRecommendations: getExperiment_experimentBySlug_signoffRecommendations | null;
  legalSignoff: boolean;
  qaSignoff: boolean;
  vpSignoff: boolean;
  onLegalSignoffChange: (value: boolean) => void;
  onQaSignoffChange: (value: boolean) => void;
  onVpSignoffChange: (value: boolean) => void;
};

const TableSignoff = ({
  signoffRecommendations,
  legalSignoff,
  qaSignoff,
  vpSignoff,
  onLegalSignoffChange,
  onQaSignoffChange,
  onVpSignoffChange,
}: TableSignoffProps) => {
  const handleLegalSignoffChange = (event: ChangeEvent<HTMLInputElement>) => {
    onLegalSignoffChange(event.target.checked);
  };

  const handleQaSignoffChange = (event: ChangeEvent<HTMLInputElement>) => {
    onQaSignoffChange(event.target.checked);
  };

  const handleVpSignoffChange = (event: ChangeEvent<HTMLInputElement>) => {
    onVpSignoffChange(event.target.checked);
  };

  return (
    <Card.Body>
      <Table data-testid="table-signoff">
        <tbody>
          <tr data-testid="table-signoff-qa">
            <th className="border-top-0">QA Sign-off</th>
            <td className="border-top-0 d-flex">
              <Form.Check
                type="checkbox"
                data-testid="is-qasignoff-checkbox"
                checked={!!qaSignoff}
                onChange={handleQaSignoffChange}
              />
              {signoffRecommendations?.qaSignoff && (
                <span className="text-success">Recommended:&nbsp; </span>
              )}
              Please file a QA request.{" "}
              <LinkExternal href={EXTERNAL_URLS.SIGNOFF_QA}>
                Learn More
              </LinkExternal>
            </td>
          </tr>
          <tr data-testid="table-signoff-vp">
            <th>VP Sign-off</th>
            <td className="d-flex">
              <Form.Check
                type="checkbox"
                data-testid="is-vpsignoff-checkbox"
                checked={!!vpSignoff}
                onChange={handleVpSignoffChange}
              />
              {signoffRecommendations?.vpSignoff && (
                <span className="text-success">Recommended:&nbsp; </span>
              )}
              Please email your VP.{" "}
              <LinkExternal href={EXTERNAL_URLS.SIGNOFF_VP}>
                Learn More
              </LinkExternal>
            </td>
          </tr>
          <tr data-testid="table-signoff-legal">
            <th>Legal Sign-off</th>
            <td className="d-flex">
              <Form.Check
                type="checkbox"
                data-testid="is-legalsignoff-checkbox"
                checked={!!legalSignoff}
                onChange={handleLegalSignoffChange}
              />
              {signoffRecommendations?.legalSignoff && (
                <span className="text-success">Recommended:&nbsp;</span>
              )}
              Please email legal.{" "}
              <LinkExternal href={EXTERNAL_URLS.SIGNOFF_LEGAL}>
                Learn More
              </LinkExternal>
            </td>
          </tr>
        </tbody>
      </Table>
    </Card.Body>
  );
};

export default TableSignoff;
