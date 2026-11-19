using Test
using Quantiles

@testset "quantile" begin
    @test quantile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.5
    @test quantile([1.0, 2.0, 3.0, 4.0], 0.0) == 1.0
    @test quantile([1.0, 2.0, 3.0, 4.0], 1.0) == 4.0
end

@testset "weighted mean" begin
    @test weighted_mean([1.0, 2.0], [1.0, 3.0]) == 1.75
end

@testset "errors" begin
    @test_throws ErrorException quantile(Float64[], 0.5)
    @test_throws ErrorException weighted_mean([1.0], [0.0])
end
