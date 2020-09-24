import { request } from "experimenter/utils/request.js";

const API_ROOT = "/api/v2/";

export function makeApiRequest(endpoint, options = {}, extraHeaders = {}) {
  return request(`${API_ROOT}${endpoint}`, options, extraHeaders);
}
