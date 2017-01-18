def subquery(event, start_date):
    return """
      {lower_event}_event AS
      (
        SELECT
          event_id,
          value
        FROM
          activity_stream_performance_daily
        WHERE
          event = '{event}' AND
          date >= '{start_date}'
      )
    """.format(lower_event=event.lower(), event=event, start_date=start_date)

def query(events, start_date):
    subqueries = ',\n'.join([subquery(event, start_date=start_date) for event in events])
    fields = ',\n'.join(['{event}_event.value as {event}'.format(event=event.lower()) for event in events])
    subtables = ',\n'.join(['{event}_event'.format(event=event.lower()) for event in events])
    joins = ' AND \n'.join(['base_event.event_id={event}_event.event_id'.format(event=event.lower()) for event in events])

    return  """
      WITH base_event AS
        (
          SELECT
            distinct(event_id),
            client_id,
            source,
            receive_at,
            addon_version,
            date
          FROM
            activity_stream_performance_daily
          WHERE
            date >= '{start_date}'
        ),
        {subqueries}
      SELECT
        base_event.client_id,
        base_event.event_id,
        base_event.receive_at,
        base_event.source,
        base_event.addon_version,
        {fields}
      FROM base_event,
        {subtables}
      WHERE
        {joins}
      LIMIT 100;
    """.format(subqueries=subqueries, fields=fields, subtables=subtables, joins=joins, start_date=start_date)


events = [
    #'embedlyProxyFailure',
    #'embedlyProxyRequestReceivedCount',
    #'embedlyProxyRequestSentCount',
    #'embedlyProxyRequestSucess',
    #'embedlyProxyRequestTime',
    #'metadataExists',
    #'metadataInvalidReceived',
    #'metadataParseFail',
    #'metadataParseSuccess',
    #'previewCacheRequest',
    #'previewCacheHits',
    #'previewCacheMisses',
    'countHistoryURLs',
    'countMetadataURLs',
]

print query(events, '01-01-2017')
