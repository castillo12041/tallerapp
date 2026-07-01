import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:taller_cliente/features/estimate/domain/entities/public_estimate.dart';
import 'package:taller_cliente/features/estimate/infrastructure/repositories/estimate_repository_impl.dart';

part 'estimate_provider.g.dart';

@riverpod
Future<PublicEstimate> publicEstimate(
  PublicEstimateRef ref,
  String token,
) async {
  final repository = EstimateRepositoryImpl();
  return repository.getPublicEstimate(token);
}

@riverpod
class EstimateRespond extends _$EstimateRespond {
  @override
  AsyncValue<void> build() => const AsyncData(null);

  Future<void> respond({
    required String token,
    required bool accepted,
    String? clientNotes,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => EstimateRepositoryImpl().respond(
        token: token,
        accepted: accepted,
        clientNotes: clientNotes,
      ),
    );
  }
}
