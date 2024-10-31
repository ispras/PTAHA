# The script transforms Rospatent search result into common format (XLSX)

library("readxl")
library("writexl")

# --- Utility functions ---

# Extracts country id from patent id at non-formatted data
GetCountry <- function(patent_id) {
  return(substr(patent_id, start = 1, stop = 2))
}

# Extracts type from patent id at non-formatted data
GetPatentType <- function(patent_id) {
  no_ws_id <- trimws(patent_id)
  patent_ids <- strsplit(no_ws_id, " ")
  patent_types <- unlist(lapply(patent_ids, function(x) x[length(x)]))
  return(patent_types)
}

# Extracts number from patent id at non-formatted data
GetPatentNum <- function(patent_id) {
  no_ws_id <- trimws(patent_id)
  patent_ids <- strsplit(no_ws_id, " ")
  ids <- lapply(patent_ids, "[[", 2)
  return(unlist(as.numeric(ids)))
}

# Extracts year from the date; it should be YYYY-MM-DD formatted
GetYear <- function(date) {
  reduced <- substr(date, start = 1, stop = 10)
  year <- substr(reduced, start = 1, stop = 4)
  return(as.numeric(year))
}

# --- Main part of the script ---

args = commandArgs(trailingOnly=TRUE)

# test if there is at least one argument: if not, return an error
if (length(args) == 0) {
  stop("At least one argument must be supplied (input file).n", call.=FALSE)
}

input_file <- args[1]

sprintf("Start transforming '%s'...", input_file)

if (!file_test("-f", input_file)) {
  sprintf("Can't find input file '%s', exit.", input_file)
  q()
}

# Rospatent data frame columns names
in_patent_id <- "Документ"
in_publ_date <- "Дата\r\nпубликации"
in_title <- "Заголовок"
in_appl_num <- "№ заявки"
in_appl_date <- "Дата\r\nподачи заявки"
in_ipc <- "МПК"
in_appl_name <- "Заявитель"
in_inventor <- "Изобретатель"
in_owner <- "Патентообладатель"

# Get input data
input_dframe <- readxl::read_excel(input_file, "Sheet1")

in_full_ids <- input_dframe[, in_patent_id]
in_ipcs <- input_dframe[, in_ipc]
in_applicants <- input_dframe[, in_appl_name]
in_inventors <- input_dframe[, in_inventor]
in_appl_nums <- input_dframe[, in_appl_num]
in_appl_dates <- input_dframe[, in_appl_date]
in_publ_dates <- input_dframe[, in_publ_date]
in_titles <- input_dframe[, in_title]

# Common format data frame columns names
out_country <- "Страна выдачи"
out_patent_type <- "Вид патента"
out_patent_num <- "Номер патента"
out_patent_id <- "Full ID"
out_url <- "Link"
out_ipc <- "Классификационный индекс"
out_classifiers <- "Классификатор(ы)"
out_search_subj <- "Предмет поиска"
out_appl_name <- "Заявитель"
out_appl_country <- "Страна заявитель"
out_inventor <- "Изобретатель"
out_appl_num <- "Номер заявки"
out_prior_date <- "Дата приоритета"
out_prior_docs <- "Приоритетные документы"
out_appl_date <- "Дата подачи заявки"
out_appl_year <- "Год подачи заявки"
out_publ_date <- "Дата публикации"
out_publ_year <- "Год публикации"
out_title <- "Название"
out_status <- "Сведения о действии"

out_col_names <- c(
  out_country, out_patent_type, out_patent_num, out_patent_id, out_url, out_ipc,
  out_classifiers, out_search_subj, out_appl_name, out_appl_country,
  out_inventor, out_appl_num, out_prior_date, out_prior_docs, out_appl_date,
  out_appl_year, out_publ_date, out_publ_year, out_title, out_status
)
out_matrix <- matrix(ncol = length(out_col_names), nrow = nrow(input_dframe))
out_dframe <- data.frame(out_matrix)

# Calculate formatted values for output dataframe
countries <- sapply(in_full_ids, GetCountry)
patent_types <- sapply(in_full_ids, GetPatentType)
patent_nums <- sapply(in_full_ids, GetPatentNum)
full_ids <- paste(countries, patent_nums, patent_types, sep = "-")
appl_years <- sapply(in_appl_dates, GetYear)
publ_years <- sapply(in_publ_dates, GetYear)

# Store values to output dataframe
colnames(out_dframe) <- out_col_names
out_dframe[, out_country] <- countries
out_dframe[, out_patent_type] <- patent_types
out_dframe[, out_patent_num] <- patent_nums
out_dframe[, out_patent_id] <- full_ids
out_dframe[, out_ipc] <- in_ipcs
out_dframe[, out_appl_name] <- in_applicants
out_dframe[, out_inventor] <- in_inventors
out_dframe[, out_appl_num] <- in_appl_nums
out_dframe[, out_appl_date] <- in_appl_dates
out_dframe[, out_appl_year] <- appl_years
out_dframe[, out_publ_date] <- in_publ_dates
out_dframe[, out_publ_year] <- publ_years
out_dframe[, out_title] <- in_titles

# Clean previous result, if exists
out_file <- "rospatent-patents.xlsx"
if (file_test("-f", out_file)) {
  file.remove(out_file)
  print("clearing previous results...done!")
}

sprintf("Writing the result to '%s'", out_file)
writexl::write_xlsx(out_dframe, out_file)

print("Transforming is complete.")
