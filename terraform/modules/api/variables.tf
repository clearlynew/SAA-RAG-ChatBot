variable "project" { type = string }
variable "region" {
  type    = string
  default = "us-east-1"
}
variable "vector_bucket_name" { type = string }
variable "vector_index_name" { type = string }
variable "vector_index_arn" { type = string }
variable "chunks_table" { type = string }
variable "terms_table" { type = string }
variable "docstats_table" { type = string }
variable "cache_table" { type = string }
variable "table_arns" { type = list(string) } # chunks, terms, docstats
variable "cache_table_arn" { type = string }

variable "cors_origins" {
  type    = list(string)
  default = ["*"] # tighten to the CloudFront domain once the frontend exists
}
variable "throttle_rate" {
  type    = number
  default = 2
}
variable "throttle_burst" {
  type    = number
  default = 5
}
variable "daily_limit" {
  type    = number
  default = 500
}
variable "reserved_concurrency" {
  type    = number
  default = -1 # no reservation. New accounts can have a low concurrency quota.
}
