import React, { useState } from "react";
import { Alert, Button, Form, Table } from "react-bootstrap";
import { CSVLink } from "react-csv";

const App: React.FC = () => {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [data, setData] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [headers, setHeaders] = useState([]);
  const onSubmit = async (): Promise<void> => {
    const response = await fetch(
      `${window.location.origin}/api/v7/${startDate}/${endDate}`,
    );
    if (response.ok) {
      const { data, headings, statistics } = await response.json();
      setData(data);
      setHeaders(headings);
      setStatistics(statistics);
    }
  };

  let summaryTable = <Alert variant="primary">There are no results to show with the time range selected</Alert>;
  if (data?.length && headers?.length) {
    summaryTable = (
      <SummaryTable
        data={data}
        endDate={endDate}
        headers={headers}
        startDate={startDate}
        statistics={statistics}
      />
    );
  }

  return (
    <div className="App">
      <h1>Experiment Reporting</h1>
      <Form inline className="mb-3">
        <Form.Group>
          <Form.Label className="mr-3" htmlFor="startDate">
            From:
          </Form.Label>
          <Form.Control
            className="mr-3"
            id="startDate"
            type="date"
            onChange={(event): void => setStartDate(event.target.value)}
          />
        </Form.Group>
        <Form.Group>
          <Form.Label className="mr-3" htmlFor="endDate">
            To:
          </Form.Label>
          <Form.Control
            className="mr-3"
            id="endDate"
            type="date"
            onChange={(event): void => setEndDate(event.target.value)}
          />
        </Form.Group>
        <Form.Group></Form.Group>
        <Button onClick={onSubmit}>Submit</Button>
      </Form>
      {summaryTable}
    </div>
  );
};

export const SummaryTable = (props): React.ReactElement => {
  const { data, headers, statistics, startDate, endDate } = props;
  const columnHeadings = headers.map((heading: string, i: number) => {
    return <th key={i}><strong>{heading}</strong></th>;
  });

  const tableRows = data.map(
    (row: Record<string, string | number | null>, i: number) => {
      return (
        <tr key={i}>
          {headers.map((header: string, i: number) => {
            return <td key={i}>{row[header]}</td>;
          })}
        </tr>
      );
    },
  );

  const computeStats = (
    stats: Record<string, Record<string, string | number>>,
  ): Array<Array<string | number>> => {
    let statsCSVData: Array<Array<string | number>> = [];
    if (stats) {
      const { status_medians: statusMedians, ...other } = stats;
      if (statusMedians) {
        statsCSVData.push(["Status Medians"]);
        const types = Object.keys(stats["status_medians"]);

        for (const type of types) {
          const typeValues = statusMedians[type];
          statsCSVData = [
            ...statsCSVData,
            [type],
            Object.keys(typeValues),
            Object.values(typeValues),
            [","],
          ];
        }
      }

      for (const otherStatKeys of Object.keys(other)) {
        const otherStatValues = other[otherStatKeys];
        statsCSVData = [
          ...statsCSVData,
          [otherStatKeys],
          Object.keys(otherStatValues),
          Object.values(otherStatValues),
          [","],
        ];
      }
    }

    return statsCSVData;
  };

  return (
    <div className="mt-2">
      <CSVLink
        className="btn btn-primary mr-2 mb-2"
        data={data}
        filename={`${startDate}-${endDate}experimenter-table.csv`}
        headers={headers}
      >
        Export Table
      </CSVLink>
      <CSVLink
        className="btn btn-success mb-2"
        data={computeStats(statistics)}
        filename={`${startDate}-${endDate}experiment-stats.csv`}
      >
        {" "}
        Export Statistics
      </CSVLink>
      <Table bordered hover>
        <thead>
          <tr>{columnHeadings}</tr>
        </thead>
        <tbody>{tableRows}</tbody>
      </Table>
    </div>
  );
};

export default App;
