module "storage" {
  source  = "./modules/storage"
  project = var.project
}
module "ingest" {
  source = "./modules/ingest"

  project            = var.project
  raw_bucket_name    = module.storage.raw_bucket
  raw_bucket_arn     = module.storage.raw_bucket_arn
  vector_bucket_name = module.storage.vector_bucket_name
  vector_index_name  = module.storage.vector_index_name
  vector_index_arn   = module.storage.vector_index_arn
  chunks_table       = module.storage.chunks_table
  terms_table        = module.storage.terms_table
  docstats_table     = module.storage.docstats_table
  table_arns         = module.storage.table_arns
}
