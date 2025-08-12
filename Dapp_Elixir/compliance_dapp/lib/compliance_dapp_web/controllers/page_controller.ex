defmodule ComplianceDappWeb.PageController do
  use ComplianceDappWeb, :controller

  def home(conn, _params) do
    render(conn, :home)
  end
end
