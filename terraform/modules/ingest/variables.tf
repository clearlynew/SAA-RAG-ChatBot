variable "project" { type = string }
variable "region" {
  type    = string
  default = "us-east-1"
}
variable "raw_bucket_name" { type = string }
variable "raw_bucket_arn" { type = string }
variable "vector_bucket_name" { type = string }
variable "vector_index_name" { type = string }
variable "vector_index_arn" { type = string }
variable "chunks_table" { type = string }
variable "terms_table" { type = string }
variable "docstats_table" { type = string }
variable "table_arns" { type = list(string) }
