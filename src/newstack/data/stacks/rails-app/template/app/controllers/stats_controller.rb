# frozen_string_literal: true

# GET /stats?text=...  answers with the wc figures as JSON.
class StatsController < ApplicationController
  def show
    text = params[:text]
    return render json: { error: "missing the text parameter" }, status: :bad_request if text.nil?

    render json: TextStat.count(text)
  end
end
